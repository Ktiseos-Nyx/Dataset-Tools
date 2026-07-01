import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { readPngParameters, writePngParameters } from '@/lib/png-metadata';

// True only when `target` is `base` itself or a real descendant of it. Uses
// path.relative instead of a raw string prefix so siblings like
// `/photos-evil` don't pass the `/photos` check. On win32, path.relative is
// case-insensitive, which is what we want for Windows paths.
function isInside(base: string, target: string): boolean {
  if (target === base) return true;
  const rel = path.relative(base, target);
  return rel.length > 0 && !rel.startsWith('..') && !path.isAbsolute(rel);
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
// existing PNG" or "create <name>_edited.png beside one".
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

    // Build target path and re-validate it against the base to prevent a
    // symlink redirect on the sibling name.
    let targetPath = sourcePath;
    if (saveAsCopy) {
      const ext = path.extname(sourcePath);
      const stem = path.basename(sourcePath, ext);
      // Underscore, not a second dot: `foo_edited.png` keeps a single-extension
      // stem so dataset/training tools that pair by stem (foo.png ↔ foo.txt) or
      // split on the first dot don't orphan the file.
      targetPath = path.join(path.dirname(sourcePath), `${stem}_edited${ext}`);
    }

    // Re-validate the final write target against the base folder and project
    // root, so a symlink on the sibling name can't redirect the write outside
    // the confined tree.
    const writeResolved = await resolveTarget(
      path.relative(PROJECT_ROOT, targetPath),
      PROJECT_ROOT,
    );
    if ('error' in writeResolved) {
      return NextResponse.json({ error: writeResolved.error }, { status: writeResolved.status });
    }

    await fs.writeFile(writeResolved.path, out);
    return NextResponse.json({ ok: true, path: path.basename(writeResolved.path) });
  } catch (error) {
    if (error instanceof Error && 'code' in error && error.code === 'ENOENT') {
      return NextResponse.json({ error: 'File not found' }, { status: 404 });
    }
    const message = error instanceof Error ? error.message : 'An unknown error occurred';
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
