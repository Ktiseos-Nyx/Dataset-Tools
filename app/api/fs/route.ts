import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

const IMAGE_EXTENSIONS = new Set([
  '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.tif',
  '.svg', '.ico', '.avif', '.heic', '.heif', '.jxl',
]);

function isImageFile(name: string): boolean {
  const ext = path.extname(name).toLowerCase();
  return IMAGE_EXTENSIONS.has(ext);
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const dirPath = searchParams.get('path') || '.';
  const showHidden = searchParams.get('showHidden') === 'true';

  // Basic security check to prevent directory traversal
  const resolvedPath = path.resolve(dirPath);
  if (!resolvedPath.startsWith(path.resolve('.'))) {
      return NextResponse.json({ error: 'Access denied' }, { status: 403 });
  }

  try {
    const files = await fs.readdir(resolvedPath, { withFileTypes: true });
    let fileList = files.map(file => ({
      name: file.name,
      isDirectory: file.isDirectory(),
    }));

    // Filter hidden files (dotfiles) unless showHidden is true
    if (!showHidden) {
      fileList = fileList.filter(file => !file.name.startsWith('.'));
    }

    // Only show directories and image files
    fileList = fileList.filter(file => file.isDirectory || isImageFile(file.name));

    return NextResponse.json(fileList);
  } catch (error) {
    if (error instanceof Error) {
        // More specific error handling
        if ('code' in error && error.code === 'ENOENT') {
            return NextResponse.json({ error: 'Directory not found' }, { status: 404 });
        }
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ error: 'An unknown error occurred' }, { status: 500 });
  }
}
