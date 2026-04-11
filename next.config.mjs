import { dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))

/** @type {import('next').NextConfig} */
const nextConfig = {
  // ✅ Keep your existing settings
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },
  reactStrictMode: true,
  
  // ✅ Turbopack config
  turbopack: { root: __dirname },
  
  // ✅ Performance tweaks
  compress: true,
  productionBrowserSourceMaps: false,
  
  // ✅ Don't bundle native addons (if you ever add sharp/onnx)
  serverExternalPackages: ['sharp', 'onnxruntime-node'],
  
  // ✅ Fix NFT tracing root (ESM-safe version)
  outputFileTracingRoot: __dirname,
  
  // ✅ Optional: Silence NFT warnings for thumbnail route
  outputFileTracingExcludes: {
    '/api/thumbnail': ['**/*'],
  },
}

export default nextConfig