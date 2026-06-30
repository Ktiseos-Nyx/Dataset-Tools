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

type Resolved = { path: string } | { error: string; status: number };

// Confine a client-supplied path to `baseFolder`.
//
// NOTE: `baseFolder` is supplied by the client by design — this is a local
// filesystem browser whose entire purpose is to operate on the folder the user
// selected, so there is no fixed server-side root to pin to. We still defend the
// write path hard: (1) lexical containment with path.relative (no prefix-match
// bypass), (2) PNG-extension gate, and (3) a symlink-aware re-check using
// fs.realpath on the concrete file so a symlink inside the base can't redirect
// the write outside it. Combined with the PNG-validity requirement downstream,
// the only writes this route can perform are "rewrite an existing PNG" or
// "create <name>.edited.png beside one".
async function resolveTarget(filePath: string, baseFolder: string): Promise<Resolved> {
  const resolvedBase = path.resolve(baseFolder || '.');
  const fullPath = path.isAbsolute(filePath) ? filePath : path.join(resolvedBase, filePath);
  const resolvedPath = path.resolve(fullPath);

  // (1) Lexical containment.
  if (!isInside(resolvedBase, resolvedPath)) {
    return { error: 'Access denied - path outside base folder', status: 403 };
  }
  // (2) PNG only.
  if (!resolvedPath.toLowerCase().endsWith('.png')) {
    return { error: 'Only PNG files are supported', status: 415 };
  }

  // (3) Symlink-aware containment. Both ends are canonicalised via realpath, so
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

// GET /api/metadata-write?path=&baseFolder=
// Returns the raw 'parameters' tEXt string to prefill the editor: { text: string | null }.
export async function GET(request: Request) {
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
// Swaps the 'parameters' tEXt chunk in place (or writes name.edited.png) without
// recompressing pixels. Returns { ok: true, path: <basename written> }.
export async function POST(request: Request) {
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

    // The copy lives in the same already-confined directory; its name is derived
    // from the source basename, so no traversal is possible here.
    let targetPath = sourcePath;
    if (saveAsCopy) {
      const ext = path.extname(sourcePath);
      const stem = path.basename(sourcePath, ext);
      targetPath = path.join(path.dirname(sourcePath), `${stem}.edited${ext}`);
    }

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
