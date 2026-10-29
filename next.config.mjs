/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },
  reactStrictMode: true,
  compress: true,
  productionBrowserSourceMaps: false,
  serverExternalPackages: ['sharp'],
  // Content-Security-Policy on every response — ported from main's
  // next.config.mjs (#221 hardening): blocks external subresources unless
  // explicitly allowlisted. 'unsafe-inline'/'unsafe-eval' on script-src are
  // required by Next's inline RSC payload and Turbopack's module runtime;
  // external scripts stay locked to same-origin. img blob:/data: covers the
  // client-side FileReader preview flow.
  async headers() {
    const csp = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://va.vercel-scripts.com",
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