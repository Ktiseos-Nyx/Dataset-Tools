// Copies static assets into the standalone build output. Next's `output:
// 'standalone'` emits a self-contained server at `.next/standalone/server.js` but
// does NOT copy `.next/static` (JS/CSS chunks) or `public` next to it — those
// must be moved manually or the packaged Electron app serves a blank page.
//
// Runs automatically as the `postbuild` npm script.
import { cpSync, existsSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs'
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

// Guard against the standalone trace missing Next's compiled Turbopack runtime.
// The runtime is loaded via a dynamic external require the tracer can't see
// (see next.config.mjs outputFileTracingIncludes). When it's absent, dev and
// `npm start` still work — require walk-up finds the file in the repo's
// node_modules — but the packaged Electron app (no parent node_modules) 500s on
// every API route. Fail loudly here instead of shipping that.
const runtimeProbe = join(
  standalone,
  'node_modules',
  'next',
  'dist',
  'compiled',
  'next-server',
  'app-route-turbo.runtime.prod.js'
)

if (!existsSync(runtimeProbe)) {
  console.error(
    '[postbuild] ERROR: standalone is missing next/dist/compiled/next-server/app-route-turbo.runtime.prod.js — ' +
      'the packaged app would 500 on every API route. Check outputFileTracingIncludes in next.config.mjs; aborting.'
  )
  process.exit(1)
}
console.log('[postbuild] compiled next-server runtime present in standalone')

// Scrub any user data the tracer may have swept into the standalone. Nov 18
// 2026: the trace copied the developer's live portable data folder
// (dist/data/.env.local — scrambled-but-decodable API keys) into the packaged
// EXE. Whatever tracer quirk causes the sweep, the artifact must never
// contain credential-bearing files — delete them and say so.
function scrubSecretFiles(dir) {
  let removed = 0
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) removed += scrubSecretFiles(full)
    else if (entry.name === '.env.local') {
      rmSync(full)
      removed++
    }
  }
  return removed
}

const scrubbed = scrubSecretFiles(standalone)
if (scrubbed > 0) {
  console.warn(
    `[postbuild] WARNING: removed ${scrubbed} .env.local file(s) that the tracer swept into the standalone. ` +
      'The packaged artifact must never contain credential files — if this recurs, run the portable EXE from outside the repo.'
  )
} else {
  console.log('[postbuild] no swept credential files in standalone')
}
