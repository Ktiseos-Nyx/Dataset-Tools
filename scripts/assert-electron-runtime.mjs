// Asserts the Electron packaging chain has everything it needs. Runs ONLY in
// the electron:build npm script — plain `npm run build` (web/CLI deployments,
// headless containers) must NOT require a bundled Node runtime (CodeRabbit PR
// #250 round 4: the postbuild gate previously fired on every Linux build and
// broke non-Electron packaging).
//
// The packaged app must ship a real Node runtime for the host OS — Electron's
// embedded Node makes every API route 500 (Oct 2026 packaging saga). Refuse to
// package a broken artifact instead of silently degrading.
import { existsSync } from 'node:fs'
import { join } from 'node:path'

const root = process.cwd()
const runtimeName = process.platform === 'win32' ? 'node.exe' : process.platform === 'linux' ? 'node-linux' : null

if (runtimeName === null) {
  // No Electron build targets on this platform (macOS ships no bundled runtime).
  console.log('[electron-pack] no bundled-runtime requirement on this platform')
  process.exit(0)
}

const runtimePath = join(root, 'build', 'node-node', runtimeName)
if (!existsSync(runtimePath)) {
  console.error(
    `[electron-pack] ERROR: build/node-node/${runtimeName} (the bundled Node v25 binary) is missing — ` +
      'the packaged app would silently fall back to Electron\u2019s embedded Node and 500 on every API route. ' +
      (process.platform === 'linux'
        ? 'Download node-v<ver>-linux-x64.tar.xz from nodejs.org and extract bin/node to build/node-node/node-linux. '
        : '') +
      'Aborting the electron build.'
  )
  process.exit(1)
}
console.log(`[electron-pack] bundled node runtime present: build/node-node/${runtimeName}`)
