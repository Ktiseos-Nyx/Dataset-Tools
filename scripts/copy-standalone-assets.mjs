// Copies static assets into the standalone build output. Next's `output:
// 'standalone'` emits a self-contained server at `.next/standalone/server.js` but
// does NOT copy `.next/static` (JS/CSS chunks) or `public` next to it — those
// must be moved manually or the packaged Electron app serves a blank page.
//
// Runs automatically as the `postbuild` npm script.
import { cpSync, existsSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const root = process.cwd()
const standalone = join(root, '.next', 'standalone')

if (!existsSync(join(standalone, 'server.js'))) {
  console.log('[postbuild] no standalone output found, skipping asset copy')
  process.exit(0)
}

const copies = [
  [join(root, '.next', 'static'), join(standalone, '.next', 'static')],
  [join(root, 'public'), join(standalone, 'public')],
]

for (const [src, dest] of copies) {
  if (!existsSync(src)) {
    console.log(`[postbuild] skip ${src} (missing)`)
    continue
  }
  cpSync(src, dest, { recursive: true })
  console.log(`[postbuild] copied ${src} -> ${dest}`)
}

// Pin the standalone server's default bind address to loopback. Next generates
// `process.env.HOSTNAME || '0.0.0.0'`, so a bare `npm start` would listen on all
// interfaces and let remote clients reach the API routes (the originGuard only
// checks the spoofable Host header, so loopback binding is the real boundary).
// The Electron main process already sets HOSTNAME=127.0.0.1; this matches that
// default for every other launch mode.
const serverPath = join(standalone, 'server.js')
const serverSrc = readFileSync(serverPath, 'utf8')
const HOSTNAME_ANY = "process.env.HOSTNAME || '0.0.0.0'"
const HOSTNAME_LOOPBACK = "process.env.HOSTNAME || '127.0.0.1'"

if (serverSrc.includes(HOSTNAME_LOOPBACK)) {
  // Already pinned from a prior build — accept as-is.
  console.log('[postbuild] standalone server already pinned to 127.0.0.1')
} else if (serverSrc.includes(HOSTNAME_ANY)) {
  writeFileSync(serverPath, serverSrc.replace(HOSTNAME_ANY, HOSTNAME_LOOPBACK))
  console.log('[postbuild] pinned standalone server to 127.0.0.1')
} else {
  // Next changed the generated server's HOSTNAME default and we can't find the
  // expected pattern — fail the build rather than silently ship a server that
  // might bind to all interfaces.
  console.error('[postbuild] ERROR: unrecognized HOSTNAME default in server.js; aborting')
  process.exit(1)
}
