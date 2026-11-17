import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'

// Under Electron the main process sets ELECTRON_USER_DATA to the per-user
// app-data dir (install dir is read-only in a packaged app). Fall back to the
// project root for dev/Vercel so existing behavior is unchanged.
const DATA_DIR = process.env.ELECTRON_USER_DATA
  ? path.resolve(process.env.ELECTRON_USER_DATA)
  : path.resolve('.')

const CONFIG_PATH = path.join(DATA_DIR, 'settings.json')
const ENV_PATH = path.join(DATA_DIR, '.env.local')

async function readConfig(): Promise<Record<string, unknown>> {
  try {
    const data = await fs.readFile(CONFIG_PATH, 'utf-8')
    return JSON.parse(data)
  } catch {
    return {}
  }
}

async function writeConfig(config: Record<string, unknown>): Promise<void> {
  await fs.writeFile(CONFIG_PATH, JSON.stringify(config, null, 2), 'utf-8')
}

async function readEnvLocal(): Promise<Record<string, string>> {
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
      env[key] = unscrambleSecret(value)
    }
    return env
  } catch {
    return {}
  }
}

async function writeEnvLocal(env: Record<string, string>): Promise<void> {
  const SECRET_KEYS = new Set(['CIVITAI_API_KEY', 'GITHUB_TOKEN'])
  const lines = Object.entries(env).map(
    ([key, value]) => `${key}=${SECRET_KEYS.has(key) ? scrambleSecret(value) : value}`
  )
  await fs.writeFile(ENV_PATH, lines.join('\n') + '\n', 'utf-8')
}

// Tier-2 obfuscation for secrets at rest: values on disk are stored as
// `enc:v1:<base64(xor(bytes, constant))>`. This is NOT encryption — the
// constant lives in this file by design, so a determined person can reverse
// it. The goal is the middle ground (Nov 18 2026 decision): someone opening
// .env.local in Notepad sees gibberish instead of "CIVITAI_API_KEY=sk-...".
// Legacy plaintext values are read transparently and re-scrambled on the
// next save, so no migration step is needed.
const SECRET_MARKER = 'enc:v1:'
const SECRET_OBFUSCATION_CONSTANT = 'knx-dataset-tools-v1-secret-scramble'

function scrambleSecret(plain: string): string {
  const bytes = Buffer.from(plain, 'utf-8')
  const keystream = Buffer.from(SECRET_OBFUSCATION_CONSTANT, 'utf-8')
  for (let i = 0; i < bytes.length; i++) bytes[i] = bytes[i] ^ keystream[i % keystream.length]
  return SECRET_MARKER + bytes.toString('base64')
}

function unscrambleSecret(stored: string): string {
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

export async function GET() {
  const config = await readConfig()
  const env = await readEnvLocal()

  return NextResponse.json({
    config,
    // Only expose whether keys exist, not the actual values
    secrets: {
      hasCivitaiApiKey: !!env.CIVITAI_API_KEY,
      hasGithubToken: !!env.GITHUB_TOKEN,
    },
  })
}

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { config, secrets } = body

    if (config) {
      const existing = await readConfig()
      await writeConfig({ ...existing, ...config })
    }

    if (secrets) {
      const env = await readEnvLocal()
      if (secrets.civitaiApiKey !== undefined) {
        if (secrets.civitaiApiKey) {
          env.CIVITAI_API_KEY = secrets.civitaiApiKey
          process.env.CIVITAI_API_KEY = secrets.civitaiApiKey
        } else {
          delete env.CIVITAI_API_KEY
          delete process.env.CIVITAI_API_KEY
        }
      }
      if (secrets.githubToken !== undefined) {
        if (secrets.githubToken) {
          env.GITHUB_TOKEN = secrets.githubToken
          // Update the running process so isGitHubSearchAvailable() and
          // searchGitHubForNode() see the new token without a restart.
          process.env.GITHUB_TOKEN = secrets.githubToken
        } else {
          delete env.GITHUB_TOKEN
          delete process.env.GITHUB_TOKEN
        }
      }
      await writeEnvLocal(env)
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Unknown error' },
      { status: 500 }
    )
  }
}