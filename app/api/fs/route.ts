import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';
import { FS_READ_DEADLINE_MS, originGuard, resolveContained } from '@/lib/fs-guard';

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

  // Desktop-only filesystem read: loopback host/origin gate + containment via
  // path.relative (shared helper, mirrors metadata-write/safetensors).
  const guardError = originGuard(request);
  if (guardError) {
    return NextResponse.json({ error: guardError }, { status: 403 });
  }
  const resolvedPath = resolveContained(baseFolder, dirPath);
  if (!resolvedPath) {
    return NextResponse.json({ error: 'Access denied - path outside base folder' }, { status: 403 });
  }

  try {
    // Node ≥20.12 supports a `signal` on readdir at runtime; @types/node@22
    // doesn't declare it — cast so the deadline applies without a types bump.
    const files = await fs.readdir(resolvedPath, {
      withFileTypes: true,
      signal: AbortSignal.timeout(FS_READ_DEADLINE_MS),
    } as unknown as { withFileTypes: true });

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
        if (error.name === 'TimeoutError') {
            return NextResponse.json({ error: 'Drive not responding (timed out reading directory)' }, { status: 504 });
        }
        return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ error: 'An unknown error occurred' }, { status: 500 });
  }
}
