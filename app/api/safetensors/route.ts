import { NextResponse } from 'next/server'
import fs from 'fs/promises'
import path from 'path'
import { createReadStream } from 'fs'
import { createHash } from 'crypto'

const MAX_HEADER_SIZE = 100 * 1024 * 1024 // 100MB sanity cap

function tryParseJson(value: string): unknown {
  try { return JSON.parse(value) } catch { return value }
}

async function computeAutoV2Hash(filePath: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const hash = createHash('sha256')
    const stream = createReadStream(filePath)
    stream.on('data', chunk => hash.update(chunk))
    stream.on('end', () => resolve(hash.digest('hex').slice(0, 10)))
    stream.on('error', reject)
  })
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const filePath = searchParams.get('path')
  const baseFolder = searchParams.get('baseFolder') || '.'
  const computeHash = searchParams.get('hash') === 'true'

  if (!filePath) {
    return NextResponse.json({ error: 'Missing path parameter' }, { status: 400 })
  }

  const resolvedBase = path.resolve(baseFolder)
  const fullPath = path.isAbsolute(filePath) ? filePath : path.join(resolvedBase, filePath)
  const resolvedPath = path.resolve(fullPath)

  if (!resolvedPath.startsWith(resolvedBase)) {
    return NextResponse.json({ error: 'Access denied' }, { status: 403 })
  }

  if (path.extname(resolvedPath).toLowerCase() !== '.safetensors') {
    return NextResponse.json({ error: 'Not a safetensors file' }, { status: 400 })
  }

  const fh = await fs.open(resolvedPath, 'r').catch(() => null)
  if (!fh) {
    return NextResponse.json({ error: 'File not found' }, { status: 404 })
  }

  try {
    // Read 8-byte little-endian u64 header length
    const lenBuf = Buffer.alloc(8)
    const { bytesRead: lenRead } = await fh.read(lenBuf, 0, 8, 0)
    if (lenRead < 8) {
      return NextResponse.json({ error: 'File too small to be a valid safetensors file' }, { status: 422 })
    }

    const headerLen = Number(lenBuf.readBigUInt64LE(0))
    if (headerLen === 0 || headerLen > MAX_HEADER_SIZE) {
      return NextResponse.json({ error: `Invalid header length: ${headerLen}` }, { status: 422 })
    }

    const headerBuf = Buffer.alloc(headerLen)
    const { bytesRead: headerRead } = await fh.read(headerBuf, 0, headerLen, 8)
    if (headerRead < headerLen) {
      return NextResponse.json({ error: 'Truncated safetensors header' }, { status: 422 })
    }

    const headerJson = JSON.parse(headerBuf.toString('utf-8'))
    const rawMeta: Record<string, string> = headerJson.__metadata__ ?? {}
    const tensorCount = Object.keys(headerJson).filter(k => k !== '__metadata__').length

    // Parse each value — many ss_ values are JSON-serialized strings
    const meta: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(rawMeta)) {
      meta[k] = typeof v === 'string' ? tryParseJson(v) : v
    }

    // LoRA architecture
    const dim = meta['ss_network_dim']
    const alpha = meta['ss_network_alpha']
    const lora = (dim !== undefined || alpha !== undefined) ? {
      networkModule: meta['ss_network_module'],
      dim: dim !== undefined ? Number(dim) : undefined,
      alpha: alpha !== undefined ? Number(alpha) : undefined,
      networkArgs: meta['ss_network_args'],
    } : undefined

    // Base model
    const modelHash = meta['ss_new_sd_model_hash'] ?? meta['ss_sd_model_hash']
    const baseModel = (meta['ss_sd_model_name'] || modelHash || meta['ss_base_model_version']) ? {
      name: meta['ss_sd_model_name'],
      hash: modelHash,
      version: meta['ss_base_model_version'],
      isV2: meta['ss_v2'] === 'True' || meta['ss_v2'] === true,
    } : undefined

    // Training params
    const trainingKeys = ['ss_learning_rate', 'ss_num_epochs', 'ss_steps', 'ss_lr_scheduler', 'ss_optimizer']
    const training = trainingKeys.some(k => meta[k] !== undefined) ? {
      learningRate: meta['ss_learning_rate'] !== undefined ? Number(meta['ss_learning_rate']) : undefined,
      unetLr: meta['ss_unet_lr'] !== undefined ? Number(meta['ss_unet_lr']) : undefined,
      textEncoderLr: meta['ss_text_encoder_lr'] !== undefined ? Number(meta['ss_text_encoder_lr']) : undefined,
      lrScheduler: meta['ss_lr_scheduler'],
      lrWarmupSteps: meta['ss_lr_warmup_steps'] !== undefined ? Number(meta['ss_lr_warmup_steps']) : undefined,
      epochs: meta['ss_num_epochs'] !== undefined ? Number(meta['ss_num_epochs']) : undefined,
      epoch: meta['ss_epoch'] !== undefined ? Number(meta['ss_epoch']) : undefined,
      steps: meta['ss_steps'] !== undefined ? Number(meta['ss_steps']) : undefined,
      batchSize: meta['ss_batch_size_per_device'] !== undefined ? Number(meta['ss_batch_size_per_device']) : undefined,
      gradientAccumulationSteps: meta['ss_gradient_accumulation_steps'] !== undefined ? Number(meta['ss_gradient_accumulation_steps']) : undefined,
      mixedPrecision: meta['ss_mixed_precision'],
      fullFp16: meta['ss_full_fp16'] === 'True' || meta['ss_full_fp16'] === true,
      maxGradNorm: meta['ss_max_grad_norm'] !== undefined ? Number(meta['ss_max_grad_norm']) : undefined,
      optimizer: meta['ss_optimizer'],
      noiseOffset: meta['ss_noise_offset'] !== undefined ? Number(meta['ss_noise_offset']) : undefined,
    } : undefined

    // Dataset
    const dataset = (meta['ss_num_train_images'] !== undefined || meta['ss_tag_frequency']) ? {
      numTrainImages: meta['ss_num_train_images'] !== undefined ? Number(meta['ss_num_train_images']) : undefined,
      numRegImages: meta['ss_num_reg_images'] !== undefined ? Number(meta['ss_num_reg_images']) : undefined,
      tagFrequency: meta['ss_tag_frequency'] as Record<string, Record<string, number>> | undefined,
      datasetDirs: meta['ss_dataset_dirs'],
    } : undefined

    // modelspec.* fields
    const specKeys = Object.keys(meta).filter(k => k.startsWith('modelspec.'))
    const modelSpec = specKeys.length > 0
      ? Object.fromEntries(specKeys.map(k => [k.replace('modelspec.', ''), meta[k]]))
      : undefined

    const result = {
      tensorCount,
      raw: meta,
      lora,
      baseModel,
      training,
      dataset,
      modelSpec,
      outputName: meta['ss_output_name'],
      autoV2Hash: computeHash ? await computeAutoV2Hash(resolvedPath) : undefined,
    }

    return NextResponse.json(result)
  } catch (error) {
    if (error instanceof SyntaxError) {
      return NextResponse.json({ error: 'Invalid JSON in safetensors header' }, { status: 422 })
    }
    return NextResponse.json({ error: error instanceof Error ? error.message : 'Unknown error' }, { status: 500 })
  } finally {
    await fh.close()
  }
}
