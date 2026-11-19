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
    // Neither readdir nor fs.promises.stat consumes options.signal (verified
    // against Node 22 source — the bindings thread only encoding/withFileTypes),
    // so the deadline is enforced on the RESPONSE — and it must cover the WHOLE
    // listing phase: the readdir AND the per-file stat fan-out below it.
    // Clearing the timer after readdir alone (the previous shape) let a pending
    // stat hang the request forever with no 504 — hit live Nov 19 2026 on a
    // cold-cache portable run against a slow drive. A stalled native read may
    // continue in the background holding one threadpool slot (bounded impact
    // with UV_THREADPOOL_SIZE raised).
    let deadlineTimer: NodeJS.Timeout | undefined
    const deadline = new Promise<never>((_, reject) => {
      deadlineTimer = setTimeout(() => {
        reject(Object.assign(new Error('Drive not responding (timed out reading directory)'), { name: 'TimeoutError' }))
      }, FS_READ_DEADLINE_MS)
    })
    const listAll = (async () => {
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

      return await Promise.all(fileListPromises);
    })();
    let fileList = await Promise.race([listAll, deadline]).finally(() => clearTimeout(deadlineTimer));

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
