import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import mime from 'mime-types';
import { FS_READ_DEADLINE_MS, originGuard, resolveContained } from '@/lib/fs-guard';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const filePath = searchParams.get('path');
  const baseFolder = searchParams.get('baseFolder') || '.';

  if (!filePath) {
    return NextResponse.json({ error: 'File path is required' }, { status: 400 });
  }

  // Desktop-only filesystem read: loopback host/origin gate + containment via
  // path.relative (shared helper, mirrors metadata-write/safetensors).
  const guardError = originGuard(request);
  if (guardError) {
    return NextResponse.json({ error: guardError }, { status: 403 });
  }
  const resolvedPath = resolveContained(baseFolder, filePath);
  if (!resolvedPath) {
    return NextResponse.json({ error: 'Access denied - path outside base folder' }, { status: 403 });
  }

  try {
    // The response deadline covers BOTH filesystem calls: the AbortSignal on
    // readFile cannot stop native I/O once it starts, and a stalled fs.stat
    // hangs with no signal at all — this timer is what guarantees the 504
    // lands. Clearing it does not cancel in-flight native I/O; a stalled read
    // may keep holding a threadpool slot in the background (bounded impact
    // with UV_THREADPOOL_SIZE raised).
    let deadlineTimer: NodeJS.Timeout | undefined
    const deadline = new Promise<never>((_, reject) => {
      deadlineTimer = setTimeout(() => {
        reject(Object.assign(new Error('Drive not responding (timed out reading file)'), { name: 'TimeoutError' }))
      }, FS_READ_DEADLINE_MS)
    })
    const io = (async () => {
      const stat = await fs.stat(resolvedPath);
      const etag = `"${stat.mtimeMs}-${stat.size}"`;
      const lastModified = new Date(stat.mtimeMs).toUTCString();

      // Return 304 if the client already has the current version
      const ifNoneMatch = request.headers.get('if-none-match');
      const ifModifiedSince = request.headers.get('if-modified-since');
      if (
        (ifNoneMatch && ifNoneMatch === etag) ||
        (!ifNoneMatch && ifModifiedSince && new Date(ifModifiedSince) >= new Date(stat.mtimeMs))
      ) {
        return { notModified: true as const, etag, lastModified };
      }

      const file = await fs.readFile(resolvedPath, { signal: AbortSignal.timeout(FS_READ_DEADLINE_MS) });
      return { notModified: false as const, etag, lastModified, file };
    })();
    const result = await Promise.race([io, deadline]).finally(() => clearTimeout(deadlineTimer));

    if (result.notModified) {
      return new NextResponse(null, {
        status: 304,
        headers: { 'ETag': result.etag, 'Last-Modified': result.lastModified, 'Cache-Control': 'private, max-age=3600' },
      });
    }

    const file = await fs.readFile(resolvedPath, { signal: AbortSignal.timeout(FS_READ_DEADLINE_MS) });
    const contentType = mime.lookup(resolvedPath) || 'application/octet-stream';

    return new NextResponse(result.file, {
      headers: {
        'Content-Type': contentType,
        'ETag': result.etag,
        'Last-Modified': result.lastModified,
        'Cache-Control': 'private, max-age=3600',
        'Content-Length': String(result.file.length),
      },
    });
  } catch (error) {
    if (error instanceof Error) {
      if ('code' in error && error.code === 'ENOENT') {
        return NextResponse.json({ error: 'File not found' }, { status: 404 });
      }
      if (error.name === 'TimeoutError' || error.name === 'AbortError') {
        return NextResponse.json({ error: 'Drive not responding (timed out reading file)' }, { status: 504 });
      }
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ error: 'An unknown error occurred' }, { status: 500 });
  }
}
