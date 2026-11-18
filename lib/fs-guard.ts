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
  let hostname = host.toLowerCase();
  if (hostname.startsWith('[')) {
    // Bracketed IPv6 literal, with or without a port: "[::1]:3000" -> "::1"
    const end = hostname.indexOf(']');
    hostname = end === -1 ? hostname.slice(1) : hostname.slice(1, end);
  } else {
    // IPv4/hostname, port stripped: "localhost:3000" -> "localhost".
    // Note a Host header is client-controlled; the loopback *binding* in the
    // dev scripts / standalone pin is the primary control, this is defense-in-depth.
    hostname = hostname.split(':')[0];
  }
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '::1';
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

/**
 * Generous deadline for filesystem reads. Slow-but-alive drives (2.5" portables
 * behind USB hubs, ~35 MB/s) legitimately take seconds and must pass; a drive
 * that never answers would otherwise hold a libuv threadpool slot AND its
 * multi-MB buffer forever, wedging the whole server — Nov 18 2026: one slow
 * portable-HDD folder poisoned healthy C: folders for the rest of the session.
 */
export const FS_READ_DEADLINE_MS = 60_000;
