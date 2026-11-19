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
export const SECRET_MARKER = 'enc:v1:'
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

// Parse .env.local verbatim: values come back exactly as stored at rest —
// secret keys keep their `enc:v1:...` marker (the encoded-value convention:
// anything with the marker is written back untouched, anything without is
// plaintext that still needs encoding). Callers that need the real secret
// decode explicitly (restoreEnvSecrets). Does NOT touch process.env (that's
// restoreEnvSecrets' job).
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
      env[key] = value
    }
    return env
  } catch {
    return {}
  }
}

// Next-compatible expansion of legacy plaintext environment references —
// the same semantics @next/env applies when it loads .env files (CodeRabbit
// PR #250: without this, saving any secret encoded a literal "${GH_TOKEN}"
// reference as the token itself, and restoreEnvSecrets would restore the
// literal string as the credential). Supported: ${VAR}, ${VAR:-fallback}
// (unset or empty), ${VAR-fallback} (unset only), bare $VAR, and escaped \$.
export function expandEnvReferences(
  value: string,
  source: Record<string, string | undefined> = process.env,
): string {
  return value.replace(
    /\\\$|\$\{([A-Za-z_][A-Za-z0-9_]*)(:?-([^}]*))?\}|\$([A-Za-z_][A-Za-z0-9_]*)/g,
    (match, braced, opWithFallback, fallback, bare) => {
      if (match === '\\$') return '$' // escaped — literal dollar
      const name = braced ?? bare
      if (braced !== undefined) {
        const colonForm = opWithFallback?.startsWith(':-') ?? false
        const resolved = source[name]
        const unset = resolved === undefined || (colonForm && resolved === '')
        if (unset && opWithFallback !== undefined) return fallback ?? ''
        if (unset) return ''
        return resolved as string
      }
      const resolved = source[name]
      return resolved === undefined ? '' : resolved
    },
  )
}

// Startup restore + runtime configuration load. Next.js loads .env.local into
// process.env in dev and `next start`, but the standalone server does NOT load
// env files itself — and the packaged artifact deliberately contains none
// (postbuild scrub, CodeRabbit PR #250 round 4). instrumentation.ts calls this
// before any request is served, so this is the established configuration-
// loading mechanism for the packaged/standalone launch path. Two cases per
// key, letting the real environment always win:
//
//  1. Secret keys (at-rest `enc:v1:...`): decode and restore the real value
//     only when the environment doesn't already supply a real plaintext value
//     (env-supplied plaintext WINS — CodeRabbit Nov 18) or still holds the
//     encoded form (e.g. an operator exported the raw file contents).
//  2. Legacy plaintext secret, absent from the environment: expand ${VAR}
//     references (Next-compatible) before exposing it — the packaged app's
//     user-data .env.local is not auto-loaded by Next.
//  3. Non-secret keys: restore into the environment when absent (the standalone
//     server has no other loader), expanded the same way.
export async function restoreEnvSecrets(): Promise<void> {
  try {
    const env = await readEnvFile()
    for (const [key, stored] of Object.entries(env)) {
      if (!stored) continue
      if (SECRET_KEYS.has(key)) {
        const current = process.env[key]
        if (stored.startsWith(SECRET_MARKER)) {
          const decoded = unscrambleSecret(stored)
          if (decoded && (!current || current.startsWith(SECRET_MARKER))) {
            process.env[key] = decoded
          }
        } else if (!current) {
          process.env[key] = expandEnvReferences(stored)
        }
      } else if (process.env[key] === undefined) {
        process.env[key] = expandEnvReferences(stored)
      }
    }
  } catch {
    // Missing or unreadable .env.local — nothing to restore.
  }
}
