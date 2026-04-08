import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

const IMAGE_EXTENSIONS = new Set([
  '.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.tif',
  '.svg', '.ico', '.avif', '.heic', '.heif', '.jxl',
]);

const MODEL_EXTENSIONS = new Set(['.safetensors']);

function isViewableFile(name: string): boolean {
  const ext = path.extname(name).toLowerCase();
  return IMAGE_EXTENSIONS.has(ext) || MODEL_EXTENSIONS.has(ext);
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const dirPath = searchParams.get('path') || '.';
  const showHidden = searchParams.get('showHidden') === 'true';
  const baseFolder = searchParams.get('baseFolder') || '.';

  // Resolve the base folder first
  const resolvedBase = path.resolve(baseFolder);

  // Build the full path: if dirPath is relative, it's relative to baseFolder
  // If dirPath is absolute, use it directly
  const fullPath = path.isAbsolute(dirPath) ? dirPath : path.join(resolvedBase, dirPath);
  const resolvedPath = path.resolve(fullPath);

  // Security: prevent directory traversal outside the base folder
  // But allow browsing any folder if it's within the selected base
  if (!resolvedPath.startsWith(resolvedBase)) {
      return NextResponse.json({ error: 'Access denied - path outside base folder' }, { status: 403 });
  }

  try {
    const files = await fs.readdir(resolvedPath, { withFileTypes: true });

    // Get file stats for sorting
    const fileListPromises = files.map(async (file) => {
      const fullPath = path.join(resolvedPath, file.name);
      try {
        const stats = await fs.stat(fullPath);
        return {
          name: file.name,
          isDirectory: file.isDirectory(),
          size: stats.size,
          mtime: stats.mtimeMs,
        };
      } catch {
        // If stat fails, return without stats
        return {
          name: file.name,
          isDirectory: file.isDirectory(),
        };
      }
    });

    let fileList = await Promise.all(fileListPromises);

    // Filter hidden files (dotfiles) unless showHidden is true
    if (!showHidden) {
      fileList = fileList.filter(file => !file.name.startsWith('.'));
    }

    // Only show directories, image files, and model files
    fileList = fileList.filter(file => file.isDirectory || isViewableFile(file.name));

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
