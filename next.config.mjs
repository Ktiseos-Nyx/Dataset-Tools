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
  // Content-Security-Policy applied to every response. `default-src 'self'`
  // blocks all external subresources (scripts, images, frames, fonts, media)
  // unless explicitly allowlisted below — the goal is locking down *external*
  // content.
  //
  // script-src carries `'unsafe-inline'` (Next.js inlines the RSC payload as
  // inline scripts) and `'unsafe-eval'` (Turbopack's module runtime uses
  // `new Function` in both dev AND production — Next 16 bundles with Turbopack
  // by default, so this is required for the app to boot at all). External
  // scripts are still locked to same-origin via `'self'`.
  async headers() {
    const csp = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://va.vercel-scripts.com",
      // framer-motion + Radix set inline style attributes (transforms, positions)
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' blob: data:",
      "connect-src 'self' https://api.github.com https://va.vercel-scripts.com",
      "font-src 'self'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'self'",
    ].join('; ')
    return [
      {
        source: '/(.*)',
        headers: [{ key: 'Content-Security-Policy', value: csp }],
      },
    ]
  },
}

export default nextConfig