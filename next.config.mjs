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
  // Content-Security-Policy applied to every response. The shipped app (Electron
  // standalone + Vercel) gets the strict policy; `next dev` only relaxes
  // script-src to admit Turbopack's hot-reload `eval`, not because the app is in
  // development but because the dev server physically injects inline/eval scripts.
  //
  // `default-src 'self'` blocks all external subresources (scripts, images,
  // frames, fonts, media) unless explicitly allowlisted below. The two external
  // origins we DO touch are the GitHub star-badge fetch and Vercel analytics.
  async headers() {
    const isProd = process.env.NODE_ENV === 'production'
    // Next.js inlines the RSC payload (`self.__next_f.push(...)`) as an inline
    // script, so `'unsafe-inline'` is required for hydration; external scripts
    // are still locked to same-origin via `'self'`.
    const scriptSrc = isProd
      ? "'self' 'unsafe-inline'"
      : "'self' 'unsafe-inline' 'unsafe-eval' https://va.vercel-scripts.com"
    const csp = [
      "default-src 'self'",
      `script-src ${scriptSrc}`,
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