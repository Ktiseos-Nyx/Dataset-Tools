import fs from 'fs/promises'
import path from 'path'

// Shared location of the app's persisted settings. Under Electron the main
// process sets ELECTRON_USER_DATA; dev/Vercel fall back to the project root.
// turbopackIgnore on the fallback resolve: without it, the instrumentation
// bundle's tracer treats the dynamic path as whole-project tracing and sweeps
// dist/ (user data, old installers — 1GB+) into the standalone (Nov 18 2026).
export const DATA_DIR = process.env.ELECTRON_USER_DATA
  ? path.resolve(process.env.ELECTRON_USER_DATA)
  : path.resolve(/* turbopackIgnore: true */ '.')
export const ENV_PATH = path.join(DATA_DIR, '.env.local')

// Only these keys get obfuscation at rest. Every other value in .env.local is
// stored and read verbatim — a non-secret value that merely starts with the
// marker must never be "decoded" (caught by CodeRabbit: a custom variable
// containing the marker would otherwise be corrupted to empty on next save).
export const SECRET_KEYS = new Set(['CIVITAI_API_KEY', 'GITHUB_TOKEN'])

// Tier-2 obfuscation for secrets at rest: values on disk are stored as
// `enc:v1:<base64(xor(bytes, constant))>`. This is NOT encryption — the
// constant lives in this file by design, so a determined person can reverse
// it. The goal is the middle ground (Nov 18 2026 decision): someone opening
// .env.local in Notepad sees gibberish instead of "CIVITAI_API_KEY=sk-...".
// Legacy plaintext values are read transparently and re-scrambled on the
// next save, so no migration step is needed.
const SECRET_MARKER = 'enc:v1:'
const SECRET_OBFUSCATION_CONSTANT = 'knx-dataset-tools-v1-secret-scramble'

export function scrambleSecret(plain: string): string {
  const bytes = Buffer.from(plain, 'utf-8')
  const keystream = Buffer.from(SECRET_OBFUSCATION_CONSTANT, 'utf-8')
  for (let i = 0; i < bytes.length; i++) bytes[i] = bytes[i] ^ keystream[i % keystream.length]
  return SECRET_MARKER + bytes.toString('base64')
}

export function unscrambleSecret(stored: string): string {
  if (!stored.startsWith(SECRET_MARKER)) return stored // legacy plaintext — passthrough
  try {
    const bytes = Buffer.from(stored.slice(SECRET_MARKER.length), 'base64')
    const keystream = Buffer.from(SECRET_OBFUSCATION_CONSTANT, 'utf-8')
    for (let i = 0; i < bytes.length; i++) bytes[i] = bytes[i] ^ keystream[i % keystream.length]
    return bytes.toString('utf-8')
  } catch {
    return '' // malformed value — treat as absent
  }
}

// Parse .env.local. Secret keys are decoded; all other values pass through
// untouched. Does NOT touch process.env (that's restoreEnvSecrets' job).
export async function readEnvFile(): Promise<Record<string, string>> {
  try {
    const data = await fs.readFile(ENV_PATH, 'utf-8')
    const env: Record<string, string> = {}
    for (const line of data.split('\n')) {
      const trimmed = line.trim()
      if (!trimmed || trimmed.startsWith('#')) continue
      const eqIdx = trimmed.indexOf('=')
      if (eqIdx === -1) continue
      const key = trimmed.slice(0, eqIdx).trim()
      let value = trimmed.slice(eqIdx + 1).trim()
      // Strip surrounding quotes
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1)
      }
      env[key] = SECRET_KEYS.has(key) ? unscrambleSecret(value) : value
    }
    return env
  } catch {
    return {}
  }
}

// Startup restore. Next.js loads .env.local into process.env verbatim, so
// obfuscated secret values would reach consumers (GitHub search, license
// lookup) as the encoded "enc:v1:..." string after every restart (caught by
// CodeRabbit). Called from instrumentation.ts before any request is served:
// decode the at-rest secrets and restore the real values into process.env.
// Legacy plaintext needs no restore — Next already loaded it correctly.
export async function restoreEnvSecrets(): Promise<void> {
  try {
    const env = await readEnvFile()
    for (const key of SECRET_KEYS) {
      const value = env[key]
      if (value) process.env[key] = value
    }
  } catch {
    // Missing or unreadable .env.local — nothing to restore.
  }
}
