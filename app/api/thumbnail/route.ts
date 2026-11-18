import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'
import sharp from 'sharp'
import { FS_READ_DEADLINE_MS, originGuard, resolveContained } from '@/lib/fs-guard'

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
const THUMB_QUEUE_WAIT_MS = 90_000
let activeThumbs = 0
const thumbQueue: Array<{ done: boolean; wake?: () => void }> = []

// Slot-transfer accounting: release() hands the slot to a waiter WITHOUT
// decrementing, so the waiter must not increment either — otherwise the count
// drifts above the cap and the pool dies permanently (caught by CodeRabbit,
// confirmed live: thumbnails stopped loading in every folder after a few
// navigations on a slow drive).
async function acquireThumbSlot(): Promise<void> {
  if (activeThumbs < MAX_CONCURRENT_THUMBS) {
    activeThumbs++
    return
  }
  const me: { done: boolean; wake?: () => void } = { done: false }
  thumbQueue.push(me)
  await new Promise<void>((resolve, reject) => {
    const timer = setTimeout(() => {
      me.done = true // release() skips us; no slot is ever transferred
      reject(Object.assign(new Error('Timed out waiting for a thumbnail slot'), { name: 'TimeoutError' }))
    }, THUMB_QUEUE_WAIT_MS)
    me.wake = () => {
      clearTimeout(timer)
      resolve()
    }
  })
  // Slot was transferred by release(); the count already reflects it.
}

function releaseThumbSlot(): void {
  while (true) {
    const next = thumbQueue.shift()
    if (!next) {
      activeThumbs--
      return
    }
    if (next.done) continue // timed-out waiter — skip, keep looking
    next.wake?.()
    return
  }
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
  // parseInt of garbage is NaN; Math.max/min keep NaN, and sharp.resize(NaN)
  // throws synchronously — guard at the source so the class dies entirely.
  const parsedSize = parseInt(searchParams.get('size') || '200', 10)
  const size = Number.isFinite(parsedSize) ? Math.min(Math.max(parsedSize, 32), 800) : 200
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

    // Generate thumbnail — one of at most MAX_CONCURRENT_THUMBS at a time.
    // Three protections stack here:
    //  - request.signal.aborted: the browser aborts on navigation; a queued
    //    request that was abandoned must not run sharp at all (503, slot
    //    released immediately).
    //  - sharp .timeout(60s): bounds the generation itself.
    //  - slot-hold race below: sharp's timer only starts after the input
    //    opens, so a stalled open could otherwise hold a slot indefinitely.
    //    On expiry the slot is released for others while the native work
    //    continues in the background (its result is discarded; it ends at the
    //    sharp timeout or when the drive finally answers).
    await acquireThumbSlot()
    try {
      if (request.signal.aborted) {
        return new NextResponse(null, { status: 503 })
      }
      let holdTimer: NodeJS.Timeout | undefined
      // Build the sharp pipeline BEFORE the deadline timer: a synchronous
      // throw (e.g. from resize) must happen while no timer is scheduled —
      // otherwise the timer's later rejection has no handler and becomes an
      // unhandled rejection that can kill the server (caught by CodeRabbit).
      const generation = sharp(resolvedPath)
        .timeout({ seconds: 60 })
        .resize(size, size, { fit: 'cover', position: 'centre' })
        .webp({ quality: 80 })
        .toBuffer()
      generation.catch(() => {}) // background failure after a deadline loss is non-fatal
      const slotDeadline = new Promise<Buffer>((_, reject) => {
        holdTimer = setTimeout(() => {
          reject(Object.assign(new Error('Timed out generating thumbnail'), { name: 'TimeoutError' }))
        }, FS_READ_DEADLINE_MS)
      })
      const buffer = await Promise.race([generation, slotDeadline]).finally(() => {
        clearTimeout(holdTimer)
      })

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
    if (error instanceof Error && (error.name === 'TimeoutError' || error.name === 'AbortError')) {
      return NextResponse.json({ error: 'Drive not responding (timed out)' }, { status: 504 })
    }
    // For any sharp processing error, fall back to full image
    return NextResponse.redirect(new URL(`/api/image?path=${encodeURIComponent(filePath)}&baseFolder=${encodeURIComponent(baseFolder)}`, request.url))
  }
}
