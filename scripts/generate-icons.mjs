// Generates the app icons electron-builder needs from a single square source
// PNG (512x512 recommended):
//   build/icon.png  — Linux AppImage (512x512)
//   build/icon.ico  — Windows (multi-size: 16/32/48/64/128/256)
//
// Usage: node scripts/generate-icons.mjs <path-to-source.png>
import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import sharp from 'sharp'
import pngToIco from 'png-to-ico'

const source = process.argv[2] ?? join(process.cwd(), 'build', 'icon-source.png')
if (!source) {
  console.error('Usage: node scripts/generate-icons.mjs <path-to-source.png>')
  process.exit(1)
}

const buildDir = join(process.cwd(), 'build')
mkdirSync(buildDir, { recursive: true })

const iconPng = await sharp(source).resize(512, 512).png().toBuffer()
writeFileSync(join(buildDir, 'icon.png'), iconPng)
console.log(`[icons] wrote build/icon.png (512x512, ${iconPng.length} bytes)`)

const sizes = [16, 32, 48, 64, 128, 256]
const frames = []
for (const size of sizes) {
  frames.push(await sharp(source).resize(size, size).png().toBuffer())
}
const ico = await pngToIco(frames)
writeFileSync(join(buildDir, 'icon.ico'), ico)
console.log(`[icons] wrote build/icon.ico (${sizes.join('/')}, ${ico.length} bytes)`)
