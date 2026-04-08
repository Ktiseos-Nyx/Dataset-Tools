/**
 * ComfyUI GitHub Node Search (Phase 2 fallback)
 *
 * When a class_type isn't in ComfyUI-Manager's extension-node-map.json, this
 * module searches GitHub for the node definition. Results are cached on disk
 * to stay within rate limits.
 *
 * Requires GITHUB_TOKEN env var (set via Settings UI). Authenticated GitHub
 * code search allows ~30 req/min vs the unauthenticated rate of 10 req/min.
 *
 * Inspired by Quadmoon's ComfyUI-Node-Finder GitHubNodeFinder
 * (https://github.com/Ktiseos-Nyx/ComfyUI-Node-Finder).
 */

import fs from 'fs/promises';
import path from 'path';
import type { NodeRepoInfo } from './comfyui-node-registry';

// ─── Cache (disk + memory) ───────────────────────────────────────────────────

interface CachedHit {
  found: true;
  repo: NodeRepoInfo;
  fetchedAt: number;
}

interface CachedMiss {
  found: false;
  fetchedAt: number;
}

type CacheRecord = CachedHit | CachedMiss;

const CACHE_DIR = path.resolve('.cache');
const CACHE_FILE = path.join(CACHE_DIR, 'comfyui-github-search.json');

// Hits live for 7 days, misses for 1 day (in case the node is published later)
const HIT_TTL_MS = 7 * 24 * 60 * 60 * 1000;
const MISS_TTL_MS = 1 * 24 * 60 * 60 * 1000;

let memoryCache: Map<string, CacheRecord> | null = null;
let cacheDirty = false;

async function loadCache(): Promise<Map<string, CacheRecord>> {
  if (memoryCache) return memoryCache;
  try {
    const data = await fs.readFile(CACHE_FILE, 'utf-8');
    const obj = JSON.parse(data) as Record<string, CacheRecord>;
    memoryCache = new Map(Object.entries(obj));
  } catch {
    memoryCache = new Map();
  }
  return memoryCache;
}

async function persistCache(): Promise<void> {
  if (!memoryCache || !cacheDirty) return;
  try {
    await fs.mkdir(CACHE_DIR, { recursive: true });
    const obj = Object.fromEntries(memoryCache);
    await fs.writeFile(CACHE_FILE, JSON.stringify(obj, null, 2), 'utf-8');
    cacheDirty = false;
  } catch (err) {
    console.error('[comfyui-github-search] Failed to persist cache:', err);
  }
}

function isExpired(entry: CacheRecord): boolean {
  const ttl = entry.found ? HIT_TTL_MS : MISS_TTL_MS;
  return Date.now() - entry.fetchedAt > ttl;
}

// ─── Rate-limit guard ────────────────────────────────────────────────────────
// GitHub code search: 30 req/min authenticated. Keep a small in-process gap
// between calls so a batch lookup can't blow the budget.

let lastRequestAt = 0;
const MIN_REQUEST_GAP_MS = 2_100; // ~28/min ceiling

async function throttle(): Promise<void> {
  const elapsed = Date.now() - lastRequestAt;
  if (elapsed < MIN_REQUEST_GAP_MS) {
    await new Promise(r => setTimeout(r, MIN_REQUEST_GAP_MS - elapsed));
  }
  lastRequestAt = Date.now();
}

// ─── GitHub search ───────────────────────────────────────────────────────────

interface GitHubCodeSearchItem {
  name: string;
  path: string;
  repository: {
    full_name: string;
    html_url: string;
    description: string | null;
    fork: boolean;
    archived: boolean;
  };
}

interface GitHubCodeSearchResponse {
  total_count: number;
  items: GitHubCodeSearchItem[];
}

/**
 * Sanitize a class_type for GitHub search by stripping characters that have
 * special meaning in the search query language. Mirrors Quadmoon's
 * `clean_name = class_name.replace('(', '')…` pre-processing.
 */
function cleanClassName(classType: string): string {
  return classType.replace(/[()[\]"']/g, '').trim();
}

/**
 * Decide whether a search hit looks like a real ComfyUI custom node and not
 * a random Python file. We accept the hit if either the repository or the
 * file path mentions "comfy" (case-insensitive). Mirrors Quadmoon's
 * `_extract_repo_info` filter.
 */
function isPlausibleComfyHit(item: GitHubCodeSearchItem): boolean {
  const repoName = item.repository.full_name.toLowerCase();
  const description = (item.repository.description || '').toLowerCase();
  const filePath = item.path.toLowerCase();
  return (
    repoName.includes('comfy') ||
    description.includes('comfy') ||
    filePath.includes('comfy')
  );
}

/**
 * Run a single GitHub code-search request and return the first plausible hit.
 * Returns null on rate-limit or no usable matches.
 */
async function fetchGitHubSearch(
  query: string,
  token: string
): Promise<GitHubCodeSearchItem | null> {
  await throttle();

  // Mirror Quadmoon's per_page=5 — small page keeps us well under the 1000-result
  // ceiling and gives the first-valid-match filter a tight working set.
  const url = `https://api.github.com/search/code?q=${encodeURIComponent(query)}&per_page=5`;

  const res = await fetch(url, {
    headers: {
      Accept: 'application/vnd.github+json',
      Authorization: `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'Dataset-Tools-ComfyUI-Node-Finder',
    },
    signal: AbortSignal.timeout(15_000),
  });

  if (res.status === 401 || res.status === 403) {
    const reset = res.headers.get('x-ratelimit-reset');
    console.warn(
      `[comfyui-github-search] GitHub returned ${res.status}` +
        (reset ? ` (rate-limit resets at ${new Date(+reset * 1000).toISOString()})` : '')
    );
    return null;
  }

  if (!res.ok) {
    console.warn(`[comfyui-github-search] GitHub returned ${res.status} for "${query}"`);
    return null;
  }

  const data: GitHubCodeSearchResponse = await res.json();
  if (!data.items || data.items.length === 0) return null;

  // Quadmoon-style first-valid-match: walk results in API order, return the
  // first one that looks like a ComfyUI custom node pack, demoting forks and
  // archived repos rather than dropping them entirely.
  const candidates = data.items
    .filter(isPlausibleComfyHit)
    .sort((a, b) => {
      const score = (item: GitHubCodeSearchItem) => {
        let s = 0;
        if (item.repository.fork) s -= 5;
        if (item.repository.archived) s -= 3;
        return s;
      };
      return score(b) - score(a);
    });

  return candidates[0] || null;
}

/**
 * Search GitHub code for a ComfyUI node class_type.
 *
 * Mirrors Quadmoon's two-stage GitHubNodeFinder:
 *   1. Loose query: `${clean_name} comfyui` — broadest net, finds nodes
 *      registered with any pattern (NODE_CLASS_MAPPINGS, decorators, etc.).
 *   2. Fallback query: `"${clean_name}" language:python` — tighter substring
 *      match against Python files when the loose query misses.
 *
 * Both queries are filtered through `isPlausibleComfyHit` so we never return
 * an unrelated Python file just because it shares the class name.
 */
async function queryGitHub(
  classType: string,
  token: string
): Promise<GitHubCodeSearchItem | null> {
  const clean = cleanClassName(classType);
  if (!clean) return null;

  // Stage 1: loose query
  const looseHit = await fetchGitHubSearch(`${clean} comfyui`, token);
  if (looseHit) return looseHit;

  // Stage 2: tighter Python-only fallback
  return fetchGitHubSearch(`"${clean}" language:python`, token);
}

function itemToRepoInfo(item: GitHubCodeSearchItem): NodeRepoInfo {
  return {
    repoUrl: item.repository.html_url,
    repoName: item.repository.full_name,
    title: item.repository.description || item.repository.full_name,
  };
}

// ─── Public API ──────────────────────────────────────────────────────────────

/**
 * Search GitHub for a ComfyUI custom node by class_type.
 * Returns null if no token is configured, the search fails, or nothing matches.
 *
 * Results are cached on disk so repeat lookups are free until the TTL expires.
 */
export async function searchGitHubForNode(
  classType: string
): Promise<NodeRepoInfo | null> {
  const token = process.env.GITHUB_TOKEN;
  if (!token) return null;

  const cache = await loadCache();
  const existing = cache.get(classType);
  if (existing && !isExpired(existing)) {
    return existing.found ? existing.repo : null;
  }

  let item: GitHubCodeSearchItem | null = null;
  try {
    item = await queryGitHub(classType, token);
  } catch (err) {
    console.error(`[comfyui-github-search] Search failed for "${classType}":`, err);
    return existing?.found ? existing.repo : null;
  }

  if (item) {
    const repo = itemToRepoInfo(item);
    cache.set(classType, { found: true, repo, fetchedAt: Date.now() });
    cacheDirty = true;
    void persistCache();
    return repo;
  }

  cache.set(classType, { found: false, fetchedAt: Date.now() });
  cacheDirty = true;
  void persistCache();
  return null;
}

/**
 * Whether GitHub fallback is currently available (i.e. token is set).
 */
export function isGitHubSearchAvailable(): boolean {
  return !!process.env.GITHUB_TOKEN;
}

/**
 * Diagnostics for the on-disk cache.
 */
export async function getGitHubSearchStats(): Promise<{
  enabled: boolean;
  cached: number;
  hits: number;
  misses: number;
}> {
  const cache = await loadCache();
  let hits = 0;
  let misses = 0;
  for (const entry of cache.values()) {
    if (entry.found) hits++;
    else misses++;
  }
  return {
    enabled: isGitHubSearchAvailable(),
    cached: cache.size,
    hits,
    misses,
  };
}

/**
 * Clear the on-disk GitHub search cache.
 */
export async function clearGitHubSearchCache(): Promise<void> {
  memoryCache = new Map();
  cacheDirty = true;
  await persistCache();
}
