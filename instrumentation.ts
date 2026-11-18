// Next.js instrumentation hook — runs once when the server boots, before any
// request is served. Restores obfuscated secrets from .env.local into
// process.env so consumers (GitHub search, license lookup) never see the
// encoded at-rest form after a restart.
export async function register() {
  const { restoreEnvSecrets } = await import('./lib/env-secrets')
  await restoreEnvSecrets()
}
