/**
 * Egress allowlist for outbound server-side fetches.
 *
 * Every external HTTP call the server makes funnels through `safeFetch`, which
 * rejects any host outside the list below. This is defense-in-depth against a
 * rogue ComfyUI node / workflow (attacker-controlled image metadata) steering
 * the server to fetch an arbitrary domain — only these known integrations are
 * ever reachable, regardless of what a crafted workflow tries to inject.
 */

const ALLOWED_FETCH_HOSTS = new Set([
  'civitai.com',
  'api.github.com',
  'raw.githubusercontent.com',
]);

function hostOf(input: string | URL | Request): string {
  const raw = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
  const host = new URL(raw).hostname.toLowerCase();
  if (!ALLOWED_FETCH_HOSTS.has(host)) {
    throw new Error(`Blocked outbound fetch to non-allowlisted host "${host}"`);
  }
  return host;
}

/**
 * Drop-in replacement for `fetch` that enforces the egress allowlist.
 * Throws synchronously (before any network I/O) for a non-allowlisted host.
 * Typed via `Parameters<typeof fetch>` so Next.js extensions like
 * `init.next.revalidate` (used by the license lookup) flow through unchanged.
 */
export async function safeFetch(
  input: Parameters<typeof fetch>[0],
  init?: Parameters<typeof fetch>[1],
): Promise<Response> {
  hostOf(input);
  return fetch(input, init);
}
