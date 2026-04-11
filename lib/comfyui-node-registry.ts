/**
 * ComfyUI Node Registry
 *
 * Fetches and caches the ComfyUI-Manager extension-node-map.json,
 * providing O(1) lookup from class_type → repo info. Also maintains
 * a list of known built-in ComfyUI node class_types.
 *
 * Data source: https://github.com/ltdrdata/ComfyUI-Manager
 */

// ─── Types ───────────────────────────────────────────────────────────────────

export interface NodeRepoInfo {
  repoUrl: string;
  repoName: string;
  title: string;
}

export type NodeClassification = 'builtin' | 'custom' | 'unknown';

export interface NodeLookupResult {
  classification: NodeClassification;
  repo?: NodeRepoInfo;
  /** How the repo info was resolved. Defaults to 'extension-map' when omitted. */
  source?: 'extension-map' | 'github';
  displayName?: string;  // ← NEW: human-readable name when repo is unknown
}

function deriveDisplayName(classType: string): string {
  // Strip common suffix words, split camelCase/underscores, take the first segment
  // e.g. "TensorArtSampler" → "TensorArt", "TA_KSampler_Node" → "TA"
  return classType
    .replace(/[_\-]?(node|sampler|loader|encode|decode|apply|advanced|simple)$/i, '')
    .replace(/([a-z])([A-Z])/g, '$1 $2')  // camelCase → words
    .split(/[_\- ]+/)[0]                   // take first segment
    .trim();
}

// ─── Built-in nodes ──────────────────────────────────────────────────────────
// Core class_types shipped with ComfyUI itself (from nodes.py + comfy_extras).
// This list covers the most common ones; unknown nodes not in this list or the
// extension map are classified as "unknown".

const BUILTIN_NODES = new Set([
  // Core samplers / scheduling
  'KSampler', 'KSamplerAdvanced', 'KSamplerSelect', 'SamplerCustom',
  'SamplerCustomAdvanced', 'SamplerDPMPP_2M_SDE', 'SamplerDPMPP_SDE',
  'SamplerDPMPP_3M_SDE', 'SamplerEulerAncestral', 'SamplerLMS',
  'SamplerDPMAdaptive', 'BasicScheduler', 'KarrasScheduler',
  'ExponentialScheduler', 'PolyexponentialScheduler', 'SDTurboScheduler',
  'VPScheduler', 'BetaSamplingScheduler', 'LaplaceScheduler',
  'SplitSigmas', 'SplitSigmasDenoise', 'FlipSigmas',

  // Loaders
  'CheckpointLoader', 'CheckpointLoaderSimple', 'unCLIPCheckpointLoader',
  'DiffusersLoader', 'UNETLoader', 'CLIPLoader', 'DualCLIPLoader',
  'TripleCLIPLoader', 'CLIPVisionLoader', 'ControlNetLoader',
  'DiffControlNetLoader', 'StyleModelLoader', 'GLIGENLoader',
  'LoraLoader', 'LoraLoaderModelOnly', 'HypernetworkLoader',
  'UpscaleModelLoader', 'VAELoader', 'PhotoMakerLoader',

  // Conditioning
  'CLIPTextEncode', 'CLIPTextEncodeSDXL', 'CLIPTextEncodeSDXLRefiner',
  'CLIPSetLastLayer', 'CLIPVisionEncode',
  'ConditioningCombine', 'ConditioningAverage', 'ConditioningConcat',
  'ConditioningSetArea', 'ConditioningSetAreaPercentage',
  'ConditioningSetAreaStrength', 'ConditioningSetMask',
  'ConditioningSetTimestepRange', 'ConditioningZeroOut',
  'ControlNetApply', 'ControlNetApplyAdvanced',
  'ControlNetApplySD3', 'SetUnionControlNetType',
  'StyleModelApply', 'GLIGENTextBoxApply',
  'unCLIPConditioning', 'InstructPixToPixConditioning',
  'PairConditioningCombine', 'PairConditioningSetDefaultCombine',
  'FluxGuidance',

  // Latent
  'EmptyLatentImage', 'EmptySD3LatentImage',
  'LatentUpscale', 'LatentUpscaleBy', 'LatentFromBatch',
  'LatentComposite', 'LatentCompositeMasked', 'LatentBlend',
  'LatentCrop', 'RepeatLatentBatch', 'RebatchLatentImages',
  'LatentBatch', 'LatentAdd', 'LatentSubtract', 'LatentMultiply',
  'LatentInterpolate', 'LatentBatchSeedBehavior',
  'LatentApplyOperation', 'LatentApplyOperationCFG',
  'LatentOperationTonemapReinhard', 'LatentOperationSharpen',

  // Image
  'LoadImage', 'LoadImageMask', 'SaveImage', 'PreviewImage',
  'ImageScale', 'ImageScaleBy', 'ImageScaleToTotalPixels',
  'ImageUpscaleWithModel', 'ImageInvert', 'ImageBatch',
  'ImageCrop', 'ImagePadForOutpaint', 'ImageCompositeMasked',
  'ImageBlend', 'ImageBlur', 'ImageQuantize',
  'ImageSharpen', 'ImageFromBatch',
  'RebatchImages', 'RepeatImageBatch',

  // Mask
  'MaskToImage', 'ImageToMask', 'ImageColorToMask',
  'SolidMask', 'InvertMask', 'CropMask', 'MaskComposite',
  'FeatherMask', 'GrowMask', 'ThresholdMask', 'MaskFromList',

  // VAE
  'VAEDecode', 'VAEEncode', 'VAEEncodeForInpaint',
  'VAEDecodeTiled', 'VAEEncodeTiled',

  // Misc / utility
  'SetLatentNoiseMask', 'LatentRotate', 'LatentFlip',
  'CLIPMergeSimple', 'CLIPMergeSubtract', 'CLIPMergeAdd',
  'ModelMergeSimple', 'ModelMergeBlocks', 'ModelMergeSubtract',
  'ModelMergeAdd', 'ModelMergeSD1', 'ModelMergeSD2', 'ModelMergeSDXL',
  'CheckpointSave', 'CLIPSave', 'VAESave',
  'FreeU', 'FreeU_V2', 'HyperTile',
  'PatchModelAddDownscale', 'ModelSamplingDiscrete',
  'ModelSamplingContinuousEDM', 'ModelSamplingContinuousV',
  'ModelSamplingStableCascade', 'ModelSamplingSD3', 'ModelSamplingFlux',
  'ModelSamplingAuraFlow', 'ModelSamplingLTXV',
  'RescaleCFG', 'PerpNeg',
  'StableCascade_EmptyLatentImage', 'StableCascade_StageB_Conditioning',
  'StableCascade_StageC_VAEEncode', 'StableZero123_Conditioning',
  'StableZero123_Conditioning_Batched', 'SV3D_Conditioning',
  'SD_4XUpscale_Conditioning',

  // Guiders (for advanced sampler workflows)
  'BasicGuider', 'CFGGuider', 'DualCFGGuider',
  'DisableNoise', 'RandomNoise',

  // Noise / sigmas
  'AddNoise',

  // SDXL-specific
  'EmptyLatentImage', // already listed but often used with SDXL

  // Primitives / reroute / notes (UI-only nodes)
  'PrimitiveNode', 'Reroute', 'Note',

  // Flux / newer built-ins
  'FluxGuidance', 'ModelSamplingFlux',
  'T5TextEncode', 'FluxTextEncode',

  // Video / AnimateDiff built-in extras
  'ImageOnlyCheckpointLoader', 'ImageOnlyCheckpointSave',
  'SVD_img2vid_Conditioning',

  // Webcam / misc
  'WebcamCapture',

  // Convert types
  'ToCPUDevice', 'ToGPUDevice',
]);

// ─── Extension node map cache ────────────────────────────────────────────────

const EXTENSION_MAP_URL =
  'https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main/extension-node-map.json';

const CACHE_TTL_MS = 6 * 60 * 60 * 1000; // 6 hours

interface CacheEntry {
  nodeIndex: Map<string, NodeRepoInfo>;
  patterns: Array<{ regex: RegExp; repo: NodeRepoInfo }>;
  fetchedAt: number;
}

let cache: CacheEntry | null = null;

/**
 * Fetch and invert the extension-node-map.json into a class_type → repo lookup.
 * Cached in memory with a TTL.
 */
async function getNodeIndex(): Promise<CacheEntry> {
  if (cache && Date.now() - cache.fetchedAt < CACHE_TTL_MS) {
    return cache;
  }

  const nodeIndex = new Map<string, NodeRepoInfo>();
  const patterns: Array<{ regex: RegExp; repo: NodeRepoInfo }> = [];

  try {
    const res = await fetch(EXTENSION_MAP_URL, {
      signal: AbortSignal.timeout(15_000),
    });

    if (!res.ok) {
      // If we have stale cache, use it rather than failing
      if (cache) return cache;
      throw new Error(`Failed to fetch extension map: ${res.status}`);
    }

    const map: Record<string, [string[], Record<string, any>]> = await res.json();

    for (const [repoUrl, [nodeNames, meta]] of Object.entries(map)) {
      // Extract a clean repo name from the URL
      const urlParts = repoUrl.replace(/\/$/, '').split('/');
      const repoName = urlParts.slice(-2).join('/'); // e.g. "owner/repo"
      const title = meta?.title_aux || meta?.title || repoName;

      const repoInfo: NodeRepoInfo = { repoUrl, repoName, title };

      for (const name of nodeNames) {
        nodeIndex.set(name, repoInfo);
      }

      // Compile nodename_pattern if present
      if (meta?.nodename_pattern) {
        try {
          patterns.push({ regex: new RegExp(meta.nodename_pattern), repo: repoInfo });
        } catch {
          // Invalid regex — skip silently
        }
      }
    }
  } catch (err) {
    // If we have stale cache, return it on network failure
    if (cache) return cache;
    // Otherwise return empty index — we degrade gracefully
    console.error('[comfyui-node-registry] Failed to fetch extension map:', err);
    cache = { nodeIndex, patterns, fetchedAt: Date.now() };
    return cache;
  }

  cache = { nodeIndex, patterns, fetchedAt: Date.now() };
  return cache;
}

// ─── Public API ──────────────────────────────────────────────────────────────

export interface LookupOptions {
  /**
   * If true and a node is unknown, fall back to a GitHub code search
   * (requires GITHUB_TOKEN env var). Results are tagged with source: 'github'.
   */
  useGitHubFallback?: boolean;
  /**
   * Maximum number of unknown nodes to resolve via the GitHub fallback in a
   * single classifyNodes call. Defaults to 5. Bounds worst-case latency on a
   * cold cache (each search is throttled to ~2s).
   */
  githubFallbackLimit?: number;
}

const DEFAULT_GITHUB_FALLBACK_LIMIT = 5;

/**
 * Look up a single node class_type. Returns classification + repo info.
 */
export async function lookupNode(
  classType: string,
  options: LookupOptions = {}
): Promise<NodeLookupResult> {
  if (BUILTIN_NODES.has(classType)) {
    return { classification: 'builtin' };
  }

  const { nodeIndex, patterns } = await getNodeIndex();

  // Exact match first
  const exact = nodeIndex.get(classType);
  if (exact) {
    return { classification: 'custom', repo: exact };
  }

  // Pattern match fallback
  for (const { regex, repo } of patterns) {
    if (regex.test(classType)) {
      return { classification: 'custom', repo };
    }
  }

  // GitHub fallback (Phase 2)
  if (options.useGitHubFallback) {
    const { searchGitHubForNode } = await import('./comfyui-github-search');
    const repo = await searchGitHubForNode(classType);
    if (repo) {
      return { classification: 'custom', repo, source: 'github' };
    }
  }

  return { classification: 'unknown', displayName: deriveDisplayName(classtype) };
}

/**
 * Classify a batch of class_types. More efficient than calling lookupNode in a
 * loop because it only fetches the index once.
 */
export async function classifyNodes(
  classTypes: string[],
  options: LookupOptions = {}
): Promise<Record<string, NodeLookupResult>> {
  const { nodeIndex, patterns } = await getNodeIndex();
  const results: Record<string, NodeLookupResult> = {};
  const unresolved: string[] = [];

  for (const classType of classTypes) {
    if (BUILTIN_NODES.has(classType)) {
      results[classType] = { classification: 'builtin' };
      continue;
    }

    const exact = nodeIndex.get(classType);
    if (exact) {
      results[classType] = { classification: 'custom', repo: exact };
      continue;
    }

    let matched = false;
    for (const { regex, repo } of patterns) {
      if (regex.test(classType)) {
        results[classType] = { classification: 'custom', repo };
        matched = true;
        break;
      }
    }

    if (!matched) {
      results[classType] = { classification: 'unknown' };
      unresolved.push(classType);
    }
  }

  // GitHub fallback (Phase 2): query unresolved nodes sequentially. The search
  // module throttles itself, but we also cap the candidate count here so a
  // workflow with hundreds of unknown class_types can't drain the rate limit
  // (or stall the request) on a cold cache.
  if (options.useGitHubFallback && unresolved.length > 0) {
    const limit = options.githubFallbackLimit ?? DEFAULT_GITHUB_FALLBACK_LIMIT;
    const cappedCandidates = unresolved.slice(0, Math.max(0, limit));
    if (cappedCandidates.length > 0) {
      const { searchGitHubForNode } = await import('./comfyui-github-search');
      for (const classType of cappedCandidates) {
        const repo = await searchGitHubForNode(classType);
        if (repo) {
          results[classType] = { classification: 'custom', repo, source: 'github' };
        }
      }
    }
  }

  return results;
}

/**
 * Check if the registry has been loaded (useful for health checks).
 */
export function isRegistryLoaded(): boolean {
  return cache !== null;
}

/**
 * Force-refresh the registry cache.
 */
export async function refreshRegistry(): Promise<void> {
  cache = null;
  await getNodeIndex();
}

/**
 * Return registry stats for diagnostics.
 */
export async function getRegistryStats(): Promise<{
  totalNodes: number;
  totalRepos: number;
  totalPatterns: number;
  builtinCount: number;
  cacheAge: number | null;
}> {
  const { nodeIndex, patterns, fetchedAt } = await getNodeIndex();
  const uniqueRepos = new Set<string>();
  for (const info of nodeIndex.values()) {
    uniqueRepos.add(info.repoUrl);
  }

  return {
    totalNodes: nodeIndex.size,
    totalRepos: uniqueRepos.size,
    totalPatterns: patterns.length,
    builtinCount: BUILTIN_NODES.size,
    cacheAge: cache ? Date.now() - fetchedAt : null,
  };
}