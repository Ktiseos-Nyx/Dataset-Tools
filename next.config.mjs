/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },
  reactStrictMode: true,
  compress: true,
  productionBrowserSourceMaps: false,
  output: 'standalone',
  // sharp is external because its native binaries (@img/sharp-*) can't be
  // bundled. chokidar stays bundled — it's pure JS, and bundling it avoids a
  // partial nft trace of its ESM/CJS dual entry points in the standalone output.
  serverExternalPackages: ['sharp'],
  // Standalone tracing can miss sharp's platform-specific native binaries
  // (@img/sharp-*), which would break thumbnails in the packaged Electron app.
  // Force them into the trace for every API route.
  outputFileTracingIncludes: {
    '/api/**/*': ['./node_modules/sharp/**/*', './node_modules/@img/**/*'],
  },
  // The API routes read user-supplied paths at runtime (`path.resolve(baseFolder)`),
  // which makes Next's tracer fall back to tracing the *entire project* into the
  // standalone output — bundling .env.local (secrets), .git, source, and caches.
  // Exclude everything that isn't needed at runtime (the compiled app already
  // lives in .next/server; node_modules is traced separately).
  outputFileTracingExcludes: {
    '/api/**/*': [
      './.git/**/*',
      './.env*',
      './.cache/**/*',
      './.thumbcache/**/*',
      './.claude/**/*',
      './.idea/**/*',
      './.remember/**/*',
      './.electron/**/*',
      './logs/**/*',
      './build/**/*',
      './dist/**/*',
      './docs/**/*',
      './scripts/**/*',
      './app/**/*',
      './components/**/*',
      './lib/**/*',
      './hooks/**/*',
      './styles/**/*',
      './types/**/*',
      './electron/**/*',
      './public/**/*',
      './*.md',
      './*.json',
      './*.mjs',
      './*.yml',
      './*.yaml',
      './*.tsbuildinfo',
      './.gitignore',
      './.gitattributes',
      './LICENSE',
    ],
  },
}

export default nextConfig