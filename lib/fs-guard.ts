import path from 'path';

/**
 * Shared hardening helpers for the desktop-only filesystem GET routes
 * (/api/fs, /api/image, /api/metadata, /api/thumbnail). Previously each route
 * duplicated a weaker `startsWith` prefix check; these are the same controls
 * /api/metadata-write and /api/safetensors already use:
 *
 * - `isInside`: containment via path.relative — a raw prefix match would let
 *   sibling folders like `/base-evil` pass a `/base` check.
 * - `originGuard`: loopback-only Host + Origin. These routes read the local
 *   disk, which is a desktop-only capability; on any public web deployment
 *   (e.g. the Vercel demo, which parses in-browser) every request is refused
 *   with 403 by design.
 */

export function isInside(base: string, target: string): boolean {
  if (target === base) return true;
  const rel = path.relative(base, target);
  return rel.length > 0 && rel !== '..' && !rel.startsWith(`..${path.sep}`) && !path.isAbsolute(rel);
}

export function isLoopbackHost(host: string): boolean {
  const hostname = host.split(':')[0].toLowerCase();
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]';
}

export function originGuard(request: Request): string | null {
  const origin = request.headers.get('origin');
  const host = request.headers.get('host');
  if (host && !isLoopbackHost(host)) {
    return 'Access denied - non-loopback host';
  }
  if (origin) {
    try {
      const originUrl = new URL(origin);
      if (!isLoopbackHost(originUrl.hostname)) {
        return 'Access denied - cross-origin request';
      }
    } catch {
      return 'Access denied - invalid origin';
    }
  }
  return null;
}

/**
 * Resolve a client-supplied path against a client-supplied baseFolder and
 * confirm the result stays inside the base. Returns the resolved absolute
 * path, or null when the request must be refused.
 */
export function resolveContained(baseFolder: string, target: string): string | null {
  const resolvedBase = path.resolve(baseFolder);
  const fullPath = path.isAbsolute(target) ? target : path.join(resolvedBase, target);
  const resolvedPath = path.resolve(fullPath);
  return isInside(resolvedBase, resolvedPath) ? resolvedPath : null;
}
