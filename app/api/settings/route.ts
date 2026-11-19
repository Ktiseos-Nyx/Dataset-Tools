import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'
import { DATA_DIR, ENV_PATH, SECRET_KEYS, SECRET_MARKER, scrambleSecret, expandEnvReferences, readEnvFile } from '@/lib/env-secrets'

const CONFIG_PATH = path.join(DATA_DIR, 'settings.json')

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
  return readEnvFile()
}

async function writeEnvLocal(env: Record<string, string>): Promise<void> {
  const lines = Object.entries(env).map(([key, value]) => {
    if (!SECRET_KEYS.has(key)) return `${key}=${value}`
    // Encoded-value convention: a value already carrying the at-rest marker
    // is written back verbatim — re-encoding it would corrupt it.
    if (value.startsWith(SECRET_MARKER)) return `${key}=${value}`
    // Plaintext (UI-supplied or legacy): resolve ${VAR} references the same
    // way @next/env expands them when loading the file, THEN encode. Without
    // this, saving one secret re-encoded a literal "${GH_TOKEN}" reference
    // as the token itself, and every consumer saw garbage after restart
    // (CodeRabbit PR #250).
    return `${key}=${scrambleSecret(expandEnvReferences(value))}`
  })
  await fs.writeFile(ENV_PATH, lines.join('\n') + '\n', 'utf-8')
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