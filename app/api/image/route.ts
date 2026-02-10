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
    const file = await fs.readFile(resolvedPath);
    const contentType = mime.lookup(resolvedPath) || 'application/octet-stream';

    return new NextResponse(file, {
      headers: {
        'Content-Type': contentType,
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
