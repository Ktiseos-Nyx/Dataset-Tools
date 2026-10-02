// Copies static assets into the standalone build output. Next's `output:
// 'standalone'` emits a self-contained server at `.next/standalone/server.js` but
// does NOT copy `.next/static` (JS/CSS chunks) or `public` next to it — those
// must be moved manually or the packaged Electron app serves a blank page.
//
// Runs automatically as the `postbuild` npm script.
import { cpSync, existsSync } from 'node:fs'
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
