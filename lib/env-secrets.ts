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

// Parse one .env file verbatim: values come back exactly as stored at rest —
// secret keys keep their `enc:v1:...` marker (the encoded-value convention:
// anything with the marker is written back untouched, anything without is
// plaintext that still needs encoding). Callers that need the real secret
// decode explicitly (restoreEnvSecrets). Does NOT touch process.env (that's
// restoreEnvSecrets' job).
export async function readEnvFile(path: string = ENV_PATH): Promise<Record<string, string>> {
  try {
    const data = await fs.readFile(path, 'utf-8')
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
// Fallback values may themselves contain references (including braced ones —
// a real brace-counting scanner, not a regex, so ${UNSET:-${BASE}/img} works)
// and are expanded recursively, bounded by MAX_EXPANSION_DEPTH so runaway
// chains terminate instead of looping (CodeRabbit PR #250 round 4).
const MAX_EXPANSION_DEPTH = 32
const NAME_START = /[A-Za-z_]/
const NAME_CHARS = /[A-Za-z0-9_]/

function matchingBrace(value: string, openIdx: number): number {
  // openIdx points at '${'; returns the index of its matching '}' or -1.
  let depth = 1
  let i = openIdx + 2
  while (i < value.length) {
    if (value[i] === '$' && value[i + 1] === '{') {
      depth++
      i += 2
      continue
    }
    if (value[i] === '}') {
      depth--
      if (depth === 0) return i
    }
    i++
  }
  return -1
}

export function expandEnvReferences(
  value: string,
  source: Record<string, string | undefined> = process.env,
  depth = 0,
): string {
  if (depth >= MAX_EXPANSION_DEPTH) return value // runaway chain — leave literal
  let out = ''
  let i = 0
  while (i < value.length) {
    if (value[i] === '\\' && value[i + 1] === '$') {
      out += '$' // escaped — literal dollar
      i += 2
      continue
    }
    if (value[i] !== '$') {
      out += value[i]
      i++
      continue
    }
    if (value[i + 1] === '{') {
      const close = matchingBrace(value, i)
      if (close === -1) {
        // Unclosed reference — emit literally and stop parsing structure.
        out += value.slice(i)
        break
      }
      const content = value.slice(i + 2, close)
      // Split NAME from operator+fallback at TOP level (nested braces in the
      // fallback don't count as the split point). ':-' checked before '-'.
      let split = -1
      let nested = 0
      for (let k = 0; k < content.length - 1; k++) {
        if (content[k] === '$' && content[k + 1] === '{') nested++
        else if (content[k] === '}') nested--
        else if (nested === 0 && content[k] === ':' && content[k + 1] === '-') { split = k; break }
        else if (nested === 0 && content[k] === '-' && NAME_CHARS.test(content[k - 1] ?? '')) { split = k; break }
      }
      const name = split === -1 ? content : content.slice(0, split)
      const op = split === -1 ? undefined : content.slice(split, split + (content[split + 1] === '-' && split + 1 < content.length && content[split] === ':' ? 2 : 1))
      const fallback = split === -1 ? undefined : content.slice(split + op!.length)
      if (!NAME_START.test(name[0] ?? '') || !/^$|^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
        // Not a valid variable reference — emit literally.
        out += value.slice(i, close + 1)
        i = close + 1
        continue
      }
      const colonForm = op?.startsWith(':-') ?? false
      const resolved = source[name]
      const unset = resolved === undefined || (colonForm && resolved === '')
      if (unset && op !== undefined) {
        out += expandEnvReferences(fallback ?? '', source, depth + 1)
      } else if (unset) {
        // No fallback and unset — empty.
      } else {
        out += resolved as string
      }
      i = close + 1
      continue
    }
    // Bare $VAR form.
    if (NAME_START.test(value[i + 1] ?? '')) {
      let k = i + 2
      while (k < value.length && NAME_CHARS.test(value[k])) k++
      const name = value.slice(i + 1, k)
      const resolved = source[name]
      out += resolved === undefined ? '' : resolved
      i = k
    } else {
      out += '$' // lone dollar — literal
      i++
    }
  }
  return out
}

// Startup restore + runtime configuration load. Next.js loads .env.local into
// process.env in dev and `next start`, but the standalone server does NOT load
// env files itself — and the packaged artifact deliberately contains none
// (postbuild scrub, CodeRabbit PR #250 round 4). instrumentation.ts calls this
// before any request is served, so this is the established configuration-
// loading mechanism for the packaged/standalone launch path. Files merge with
// Next's precedence — .env < .env.production < .env.local — so a CLI user's
// .env.production config keeps working after the scrub (CodeRabbit round 4).
// Cases per key, letting the real environment always win:
//
//  1. Secret keys (at-rest `enc:v1:...`): decode and restore the real value
//     only when the environment doesn't already supply a real plaintext value
//     (env-supplied plaintext WINS — CodeRabbit Nov 18) or still holds the
//     encoded form (e.g. an operator exported the raw file contents).
//  2. Legacy plaintext secret, absent from the environment: expand ${VAR}
//     references (Next-compatible) before exposing it.
//  3. Non-secret keys: restore into the environment when absent (the standalone
//     server has no other loader), expanded the same way.
// Reference resolution uses the MERGED file values plus the real environment
// (file values win for lookups, matching @next/env's chained-reference
// semantics), so GITHUB_TOKEN=${GH_TOKEN} resolves even when GH_TOKEN is
// defined later in the same file (CodeRabbit round 4).
export async function restoreEnvSecrets(): Promise<void> {
  try {
    const merged: Record<string, string> = {}
    for (const file of ['.env', '.env.production', '.env.local'] as const) {
      Object.assign(merged, await readEnvFile(path.join(DATA_DIR, file)))
    }
    // File values win over process.env for REFERENCE lookups (a file line
    // referencing a sibling line must resolve from the file, @next/env-style);
    // final assignment precedence below still lets env-supplied values win.
    const source: Record<string, string | undefined> = { ...process.env, ...merged }
    for (const [key, stored] of Object.entries(merged)) {
      if (!stored) continue
      if (SECRET_KEYS.has(key)) {
        const current = process.env[key]
        if (stored.startsWith(SECRET_MARKER)) {
          const decoded = unscrambleSecret(stored)
          if (decoded && (!current || current.startsWith(SECRET_MARKER))) {
            process.env[key] = decoded
          }
        } else if (!current) {
          process.env[key] = expandEnvReferences(stored, source)
        }
      } else if (process.env[key] === undefined) {
        process.env[key] = expandEnvReferences(stored, source)
      }
    }
  } catch {
    // Missing or unreadable env files — nothing to restore.
  }
}
