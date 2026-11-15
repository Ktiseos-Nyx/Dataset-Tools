import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { readPngParameters, writePngParameters, isPng } from '@/lib/png-metadata';

// True only when `target` is `base` itself or a real descendant of it. Uses
// path.relative instead of a raw string prefix so siblings like
// `/photos-evil` don't pass the `/photos` check. On win32, path.relative is
// case-insensitive, which is what we want for Windows paths.
function isInside(base: string, target: string): boolean {
  if (target === base) return true;
  const rel = path.relative(base, target);
  return rel.length > 0 && rel !== '..' && !rel.startsWith(`..${path.sep}`) && !path.isAbsolute(rel);
}

const PROJECT_ROOT = path.resolve(process.cwd());

type Resolved = { path: string } | { error: string; status: number };

// Confine a client-supplied path to `baseFolder`.
//
// NOTE: `baseFolder` is supplied by the client by design — this is a local
// filesystem browser whose entire purpose is to operate on the folder the user
// selected, so there is no fixed server-side root to pin to. We still defend the
// write path hard: (1) lexical containment with path.relative (no prefix-match
// bypass), (2) a project-root containment layer so arbitrary baseFolders can't
// reach outside the repo, (3) PNG-extension gate, and (4) a symlink-aware
// re-check using fs.realpath on the concrete file so a symlink inside the base
// can't redirect the write outside it. Combined with the PNG-validity
// requirement downstream, the only writes this route can perform are "rewrite an
// existing PNG" or "create <name>_edited.png beside one" — the copy is strict
// exclusive-create ('wx'): an existing sibling, file or symlink, is refused
// rather than followed (owner decision on #235, Nov 2026). Writes require the
// app's exact origin + an application/json content type (POST only).
async function resolveTarget(filePath: string, baseFolder: string): Promise<Resolved> {
  const resolvedBase = path.resolve(baseFolder || '.');
  const fullPath = path.isAbsolute(filePath) ? filePath : path.join(resolvedBase, filePath);
  const resolvedPath = path.resolve(fullPath);

  // (1) Project-root containment — defense in depth so a client-supplied
  //     baseFolder can't reach outside the repo.
  if (!isInside(PROJECT_ROOT, resolvedBase)) {
    return { error: 'Access denied - base folder outside project root', status: 403 };
  }

  // (2) Lexical containment within baseFolder.
  if (!isInside(resolvedBase, resolvedPath)) {
    return { error: 'Access denied - path outside base folder', status: 403 };
  }
  // (3) PNG only.
  if (!resolvedPath.toLowerCase().endsWith('.png')) {
    return { error: 'Only PNG files are supported', status: 415 };
  }

  // (4) Symlink-aware containment. Both ends are canonicalised via realpath, so
  // a base reached through a symlink/junction still works (its files canonicalise
  // consistently), while a file that escapes the base via a symlink is rejected.
  let realBase: string;
  try {
    realBase = await fs.realpath(resolvedBase);
  } catch {
    return { error: 'Base folder not found', status: 404 };
  }
  let realPath: string;
  try {
    realPath = await fs.realpath(resolvedPath);
  } catch {
    return { error: 'File not found', status: 404 };
  }
  if (!isInside(realBase, realPath)) {
    return { error: 'Access denied - path escapes base folder', status: 403 };
  }

  // (5) Canonical project-root containment. Layer (1) is lexical only, so a
  // base reached through an in-project folder symlink pointing outside the
  // repo passes (1) while its canonical files live outside PROJECT_ROOT.
  // Since every write decision downstream uses the canonical path returned
  // here, containment must hold for the canonical path too.
  let realRoot: string;
  try {
    realRoot = await fs.realpath(PROJECT_ROOT);
  } catch {
    realRoot = PROJECT_ROOT;
  }
  if (!isInside(realRoot, realPath)) {
    return { error: 'Access denied - path outside project root', status: 403 };
  }

  // (6) Canonical PNG check. Layer (3) checks the lexical name only; a
  // `foo.png` symlink pointing at PNG bytes stored as `foo.txt` would
  // canonicalise to a .txt and let the copy flow derive a `_edited.txt`
  // sibling the file browser then hides. Check the canonical name.
  if (!realPath.toLowerCase().endsWith('.png')) {
    return { error: 'Only PNG files are supported', status: 415 };
  }

  return { path: realPath };
}

function isLoopbackHost(host: string): boolean {
  const hostname = host.split(':')[0].toLowerCase();
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]';
}

function originGuard(request: Request): string | null {
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

// GET /api/metadata-write?path=&baseFolder=
// Returns the raw 'parameters' tEXt string to prefill the editor: { text: string | null }.
export async function GET(request: Request) {
  const guardError = originGuard(request);
  if (guardError) {
    return NextResponse.json({ error: guardError }, { status: 403 });
  }

  const { searchParams } = new URL(request.url);
  const filePath = searchParams.get('path');
  const baseFolder = searchParams.get('baseFolder') || '.';

  if (!filePath) {
    return NextResponse.json({ error: 'File path is required' }, { status: 400 });
  }
  const resolved = await resolveTarget(filePath, baseFolder);
  if ('error' in resolved) {
    return NextResponse.json({ error: resolved.error }, { status: resolved.status });
  }

  try {
    const buf = await fs.readFile(resolved.path);
    if (!isPng(buf)) {
      return NextResponse.json({ error: 'Not a valid PNG file' }, { status: 415 });
    }
    return NextResponse.json({ text: readPngParameters(buf) });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'An unknown error occurred';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

// POST /api/metadata-write  { path, baseFolder, text, saveAsCopy? }
// Swaps the 'parameters' tEXt chunk in place (or writes name_edited.png) without
// recompressing pixels. Returns { ok: true, path: <basename written> }.
export async function POST(request: Request) {
  const guardError = originGuard(request);
  if (guardError) {
    return NextResponse.json({ error: guardError }, { status: 403 });
  }

  // CSRF hardening (#234): the guard above only requires *a* loopback origin,
  // but every local port qualifies. A page on another loopback port could
  // otherwise forge a browser-simple write (text/plain body — request.json()
  // parses it regardless of content type). For writes we require an Origin
  // header whose full origin (scheme + host + port) equals our own trusted
  // origin, plus an application/json content type. The app's renderer always
  // sends all of these; non-browser writers must now mimic them, which is
  // fine — the threat this blocks is other *browser pages* on the same machine.
  const origin = request.headers.get('origin');
  const host = request.headers.get('host');
  if (!host || !origin) {
    return NextResponse.json({ error: 'Access denied - browser origin required for writes' }, { status: 403 });
  }
  let originUrl: URL;
  try {
    originUrl = new URL(origin);
  } catch {
    return NextResponse.json({ error: 'Access denied - invalid origin' }, { status: 403 });
  }
  // The server is loopback-only and has no TLS termination, so the trusted
  // scheme is http unless a (future) proxy says otherwise via x-forwarded-proto.
  const proto = (request.headers.get('x-forwarded-proto') || 'http').toLowerCase();
  const trustedOrigin = `${proto}://${host.toLowerCase()}`;
  if (originUrl.origin.toLowerCase() !== trustedOrigin) {
    return NextResponse.json({ error: 'Access denied - cross-origin write' }, { status: 403 });
  }
  // Compare the media type proper (the part before any parameters), not a
  // substring: `application/json` with a charset param passes, but impostor
  // types like `application/json-patch+json` do not.
  const contentType = (request.headers.get('content-type') || '').toLowerCase();
  const mediaType = contentType.split(';')[0].trim();
  if (mediaType !== 'application/json') {
    return NextResponse.json({ error: 'Content-Type must be application/json' }, { status: 415 });
  }

  let body: { path?: string; baseFolder?: string; text?: string; saveAsCopy?: boolean };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { path: filePath, baseFolder = '.', text, saveAsCopy = false } = body;
  if (!filePath || typeof text !== 'string') {
    return NextResponse.json({ error: 'path and text are required' }, { status: 400 });
  }

  const resolved = await resolveTarget(filePath, baseFolder);
  if ('error' in resolved) {
    return NextResponse.json({ error: resolved.error }, { status: resolved.status });
  }
  const sourcePath = resolved.path;

  try {
    const stat = await fs.stat(sourcePath);
    if (!stat.isFile()) {
      return NextResponse.json({ error: 'Target is not a file' }, { status: 400 });
    }

    const buf = await fs.readFile(sourcePath);
    // Throws on a non-PNG, so the only bytes this route ever writes are a valid
    // PNG derived from an existing PNG at this location.
    const out = writePngParameters(buf, text);

    // Build the target path from the canonical source: same directory, same
    // canonical .png extension, so the sibling can neither escape the
    // canonical base nor carry a non-PNG name.
    let targetPath = sourcePath;
    if (saveAsCopy) {
      const ext = path.extname(sourcePath);
      const stem = path.basename(sourcePath, ext);
      // Underscore, not a second dot: `foo_edited.png` keeps a single-extension
      // stem so dataset/training tools that pair by stem (foo.png ↔ foo.txt) or
      // split on the first dot don't orphan the file.
      targetPath = path.join(path.dirname(sourcePath), `${stem}_edited${ext}`);
    }

    // Save-as-copy is strict exclusive-create (#235, owner decision Nov 2026):
    // the 'wx' flag fails with EEXIST if the sibling already exists — as a
    // regular file OR a symlink — and O_EXCL creation does not follow a
    // symlink planted at the path between check and write, because the
    // creation IS the check: no lstat-then-write race window exists. Repeat
    // copy-saves require deleting the old copy first (by design).
    if (saveAsCopy) {
      try {
        await fs.writeFile(targetPath, out, { flag: 'wx' });
      } catch (writeError) {
        if (
          writeError instanceof Error &&
          'code' in writeError &&
          writeError.code === 'EEXIST'
        ) {
          return NextResponse.json(
            { error: 'Copy already exists - delete the old _edited copy first' },
            { status: 409 },
          );
        }
        throw writeError;
      }
      return NextResponse.json({ ok: true, path: path.basename(targetPath) });
    }

    // In-place save overwrites the canonical source itself, which resolveTarget
    // already validated as a real file inside the canonical tree.
    await fs.writeFile(targetPath, out);
    return NextResponse.json({ ok: true, path: path.basename(targetPath) });
  } catch (error) {
    if (error instanceof Error && 'code' in error && error.code === 'ENOENT') {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }
    const message = error instanceof Error ? error.message : 'An unknown error occurred';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
