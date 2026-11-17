import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'
import sharp from 'sharp'
import { originGuard, resolveContained } from '@/lib/fs-guard'

// Under Electron, the thumbnail cache lives in the per-user app-data dir so a
// packaged app's read-only install dir isn't written to.
const CACHE_DIR = process.env.ELECTRON_USER_DATA
  ? path.join(process.env.ELECTRON_USER_DATA, '.thumbcache')
  : path.resolve(/* turbopackIgnore: true */ '.thumbcache')

// Generate at most a few thumbnails at a time. The viewport fires every image
// in a folder at once; on a slow external drive (USB-hub'd 2.5" portables are
// the worst case) that flood saturates Node's 4-thread libuv pool, spikes RAM
// with in-flight pixel buffers, and starves every other route (Nov 18 2026).
// Queued requests hold no resources — only active generations do.
const MAX_CONCURRENT_THUMBS = 3
let activeThumbs = 0
const thumbQueue: Array<() => void> = []

async function acquireThumbSlot(): Promise<void> {
  if (activeThumbs < MAX_CONCURRENT_THUMBS) {
    activeThumbs++
    return
  }
  await new Promise<void>(resolve => thumbQueue.push(resolve))
  activeThumbs++
}

function releaseThumbSlot(): void {
  const next = thumbQueue.shift()
  if (next) next() // wakes an acquire, which does the increment
  else activeThumbs--
}

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

  // Desktop-only filesystem read: loopback host/origin gate + containment via
  // path.relative (shared helper, mirrors metadata-write/safetensors).
  const guardError = originGuard(request)
  if (guardError) {
    return NextResponse.json({ error: guardError }, { status: 403 })
  }
  const resolvedPath = resolveContained(baseFolder, filePath)
  if (!resolvedPath) {
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

    // Generate thumbnail — one of at most MAX_CONCURRENT_THUMBS at a time,
    // with a generous deadline so a drive that never answers can't hold a
    // slot forever (sharp reads the file itself, so its own timeout applies).
    await acquireThumbSlot()
    try {
      const buffer = await sharp(resolvedPath)
        .timeout({ seconds: 60 })
        .resize(size, size, { fit: 'cover', position: 'centre' })
        .webp({ quality: 80 })
        .toBuffer()

      // Write to cache (fire-and-forget)
      fs.writeFile(cachePath, buffer).catch(() => {})

      return new NextResponse(new Uint8Array(buffer), {
        headers: {
          'Content-Type': 'image/webp',
          'Cache-Control': 'public, max-age=86400',
        },
      })
    } finally {
      releaseThumbSlot()
    }
  } catch (error) {
    if (error instanceof Error && 'code' in error && (error as NodeJS.ErrnoException).code === 'ENOENT') {
      return NextResponse.json({ error: 'File not found' }, { status: 404 })
    }
    // For any sharp processing error, fall back to full image
    return NextResponse.redirect(new URL(`/api/image?path=${encodeURIComponent(filePath)}&baseFolder=${encodeURIComponent(baseFolder)}`, request.url))
  }
}
