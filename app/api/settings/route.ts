import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'

const CONFIG_PATH = path.resolve('settings.json')
const ENV_PATH = path.resolve('.env.local')

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
      env[key] = value
    }
    return env
  } catch {
    return {}
  }
}

async function writeEnvLocal(env: Record<string, string>): Promise<void> {
  const lines = Object.entries(env).map(([key, value]) => `${key}=${value}`)
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
        } else {
          delete env.CIVITAI_API_KEY
        }
      }
      if (secrets.githubToken !== undefined) {
        if (secrets.githubToken) {
          env.GITHUB_TOKEN = secrets.githubToken
        } else {
          delete env.GITHUB_TOKEN
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
