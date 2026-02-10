import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'
import sharp from 'sharp'

const CACHE_DIR = path.resolve('.thumbcache')

// Extensions sharp can reliably handle
const SHARP_SUPPORTED = new Set([
  '.png', '.jpg', '.jpeg', '.webp', '.gif', '.tiff', '.tif', '.avif',
])

async function ensureCacheDir() {
  try {
    await fs.mkdir(CACHE_DIR, { recursive: true })
  } catch {
    // already exists
  }
}

function getCachePath(filePath: string, size: number): string {
  // Create a safe filename from the path
  const safe = filePath.replace(/[^a-zA-Z0-9._-]/g, '_')
  return path.join(CACHE_DIR, `${safe}_${size}.webp`)
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const filePath = searchParams.get('path')
  const size = Math.min(Math.max(parseInt(searchParams.get('size') || '200', 10), 32), 800)
  const baseFolder = searchParams.get('baseFolder') || '.'

  if (!filePath) {
    return NextResponse.json({ error: 'path is required' }, { status: 400 })
  }

  // Resolve the base folder first
  const resolvedBase = path.resolve(baseFolder)

  // Build the full path
  const fullPath = path.isAbsolute(filePath) ? filePath : path.join(resolvedBase, filePath)
  const resolvedPath = path.resolve(fullPath)

  // Security: prevent directory traversal outside the base folder
  if (!resolvedPath.startsWith(resolvedBase)) {
    return NextResponse.json({ error: 'Access denied - path outside base folder' }, { status: 403 })
  }

  // Check if sharp supports this format
  const ext = path.extname(resolvedPath).toLowerCase()
  if (!SHARP_SUPPORTED.has(ext)) {
    // For unsupported formats (SVG, HEIC, etc.), redirect to the full image endpoint
    return NextResponse.redirect(new URL(`/api/image?path=${encodeURIComponent(filePath)}&baseFolder=${encodeURIComponent(baseFolder)}`, request.url))
  }

  try {
    await ensureCacheDir()
    const cachePath = getCachePath(filePath, size)

    // Check cache validity: does cached thumb exist and is it newer than source?
    try {
      const [srcStat, thumbStat] = await Promise.all([
        fs.stat(resolvedPath),
        fs.stat(cachePath),
      ])
      if (thumbStat.mtimeMs >= srcStat.mtimeMs) {
        // Serve cached thumbnail
        const data = await fs.readFile(cachePath)
        return new NextResponse(data, {
          headers: {
            'Content-Type': 'image/webp',
            'Cache-Control': 'public, max-age=86400',
          },
        })
      }
    } catch {
      // Cache miss or source doesn't exist yet, generate below
    }

    // Generate thumbnail
    const buffer = await sharp(resolvedPath)
      .resize(size, size, { fit: 'cover', position: 'centre' })
      .webp({ quality: 80 })
      .toBuffer()

    // Write to cache (fire-and-forget)
    fs.writeFile(cachePath, buffer).catch(() => {})

    return new NextResponse(buffer, {
      headers: {
        'Content-Type': 'image/webp',
        'Cache-Control': 'public, max-age=86400',
      },
    })
  } catch (error) {
    if (error instanceof Error && 'code' in error && (error as NodeJS.ErrnoException).code === 'ENOENT') {
      return NextResponse.json({ error: 'File not found' }, { status: 404 })
    }
    // For any sharp processing error, fall back to full image
    return NextResponse.redirect(new URL(`/api/image?path=${encodeURIComponent(filePath)}&baseFolder=${encodeURIComponent(baseFolder)}`, request.url))
  }
}
