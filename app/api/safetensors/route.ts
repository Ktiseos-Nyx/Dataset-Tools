import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'
import { createReadStream } from 'fs'
import { createHash } from 'crypto'
import { buildSafetensorsView } from '@/lib/safetensors-parse'

const MAX_HEADER_SIZE = 100 * 1024 * 1024 // 100MB sanity cap

async function computeAutoV2Hash(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const hash = createHash('sha256')
    const stream = createReadStream(filePath)
    stream.on('data', chunk => hash.update(chunk))
    stream.on('end', () => resolve(hash.digest('hex').slice(0, 10)))
    stream.on('error', reject)
  })
}

// Confine a client-supplied path to baseFolder using path.relative. A raw
// string prefix check would let sibling folders like `/base-evil` pass a
// `/base` check — the same containment metadata-write uses.
function isInside(base: string, target: string): boolean {
  if (target === base) return true
  const rel = path.relative(base, target)
  return rel.length > 0 && rel !== '..' && !rel.startsWith(`..${path.sep}`) && !path.isAbsolute(rel)
}

function isLoopbackHost(host: string): boolean {
  const hostname = host.split(':')[0].toLowerCase()
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]'
}

// This route reads files from disk — a desktop-only capability. It is safe on
// the local app (loopback host/origin) and inert on any public web deployment,
// where every request is refused with 403. Mirrors metadata-write's originGuard.
function originGuard(request: Request): string | null {
  const origin = request.headers.get('origin')
  const host = request.headers.get('host')
  if (host && !isLoopbackHost(host)) {
    return 'Access denied - non-loopback host'
  }
  if (origin) {
    try {
      const originUrl = new URL(origin)
      if (!isLoopbackHost(originUrl.hostname)) {
        return 'Access denied - cross-origin request'
      }
    } catch {
      return 'Access denied - invalid origin'
    }
  }
  return null
}

export async function GET(request: Request) {
  const guardError = originGuard(request)
  if (guardError) {
    return NextResponse.json({ error: guardError }, { status: 403 })
  }

  const { searchParams } = new URL(request.url)
  const filePath = searchParams.get('path')
  const baseFolder = searchParams.get('baseFolder') || '.'
  const computeHash = searchParams.get('hash') === 'true'

  if (!filePath) {
    return NextResponse.json({ error: 'Missing path parameter' }, { status: 400 })
  }

  const resolvedBase = path.resolve(baseFolder)
  const fullPath = path.isAbsolute(filePath) ? filePath : path.join(resolvedBase, filePath)
  const resolvedPath = path.resolve(fullPath)

  if (!isInside(resolvedBase, resolvedPath)) {
    return NextResponse.json({ error: 'Access denied' }, { status: 403 })
  }

  if (path.extname(resolvedPath).toLowerCase() !== '.safetensors') {
    return NextResponse.json({ error: 'Not a safetensors file' }, { status: 400 })
  }

  // Symlink-aware re-check: a symlink/junction inside the base folder must not
  // redirect the read outside it.
  let realBase: string
  try {
    realBase = await fs.realpath(resolvedBase)
  } catch {
    return NextResponse.json({ error: 'Base folder not found' }, { status: 404 })
  }
  let realPath: string
  try {
    realPath = await fs.realpath(resolvedPath)
  } catch {
    return NextResponse.json({ error: 'File not found' }, { status: 404 })
  }
  if (!isInside(realBase, realPath)) {
    return NextResponse.json({ error: 'Access denied - path escapes base folder' }, { status: 403 })
  }

  const fh = await fs.open(realPath, 'r').catch(() => null)
  if (!fh) {
    return NextResponse.json({ error: 'File not found' }, { status: 404 })
  }

  try {
    // Read 8-byte little-endian u64 header length
    const lenBuf = Buffer.alloc(8)
    const { bytesRead: lenRead } = await fh.read(lenBuf, 0, 8, 0)
    if (lenRead < 8) {
      return NextResponse.json({ error: 'File too small to be a valid safetensors file' }, { status: 422 })
    }

    const headerLen = Number(lenBuf.readBigUInt64LE(0))
    if (headerLen === 0 || headerLen > MAX_HEADER_SIZE) {
      return NextResponse.json({ error: `Invalid header length: ${headerLen}` }, { status: 422 })
    }

    const headerBuf = Buffer.alloc(headerLen)
    const { bytesRead: headerRead } = await fh.read(headerBuf, 0, headerLen, 8)
    if (headerRead < headerLen) {
      return NextResponse.json({ error: 'Truncated safetensors header' }, { status: 422 })
    }

    const headerJson = JSON.parse(headerBuf.toString('utf-8'))
    const rawMeta: Record<string, string> = headerJson.__metadata__ ?? {}
    const tensorCount = Object.keys(headerJson).filter(k => k !== '__metadata__').length

    const result = buildSafetensorsView({
      rawMeta,
      tensorCount,
      autoV2Hash: computeHash ? await computeAutoV2Hash(realPath) : undefined,
    })

    return NextResponse.json(result)
  } catch (error) {
    if (error instanceof SyntaxError) {
      return NextResponse.json({ error: 'Invalid JSON in safetensors header' }, { status: 422 })
    }
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Unknown error' }, { status: 500 })
  } finally {
    await fh.close()
  }
}
