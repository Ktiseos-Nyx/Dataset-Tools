import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import mime from 'mime-types';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const filePath = searchParams.get('path');
  const baseFolder = searchParams.get('baseFolder') || '.';

  if (!filePath) {
    return NextResponse.json({ error: 'File path is required' }, { status: 400 });
  }

  // Resolve the base folder first
  const resolvedBase = path.resolve(baseFolder);

  // Build the full path
  const fullPath = path.isAbsolute(filePath) ? filePath : path.join(resolvedBase, filePath);
  const resolvedPath = path.resolve(fullPath);

  // Security: prevent directory traversal outside the base folder
  if (!resolvedPath.startsWith(resolvedBase)) {
    return NextResponse.json({ error: 'Access denied - path outside base folder' }, { status: 403 });
  }

  try {
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
      return new NextResponse(null, {
        status: 304,
        headers: { 'ETag': etag, 'Last-Modified': lastModified, 'Cache-Control': 'private, max-age=3600' },
      });
    }

    const file = await fs.readFile(resolvedPath);
    const contentType = mime.lookup(resolvedPath) || 'application/octet-stream';

    return new NextResponse(file, {
      headers: {
        'Content-Type': contentType,
        'ETag': etag,
        'Last-Modified': lastModified,
        'Cache-Control': 'private, max-age=3600',
        'Content-Length': String(stat.size),
      },
    });
  } catch (error) {
    if (error instanceof Error) {
      if ('code' in error && error.code === 'ENOENT') {
        return NextResponse.json({ error: 'File not found' }, { status: 404 });
      }
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ error: 'An unknown error occurred' }, { status: 500 });
  }
}
