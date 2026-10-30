// Shared safetensors header mapping — used by the /api/safetensors route
// (desktop/server reads) and by the browser-local reader (a folder picked via
// the File System Access API or webkitdirectory). One mapping, one truth.
import type { SafetensorsMetadata } from '@/types/safetensors'

export const MAX_HEADER_SIZE = 100 * 1024 * 1024 // 100MB sanity cap

function tryParseJson(value: string): unknown {
  try { return JSON.parse(value) } catch { return value }
}

export interface SafetensorsViewInput {
  rawMeta: Record<string, string>
  tensorCount: number
  autoV2Hash?: string
}

/** Turn raw `__metadata__` entries + tensor count into the display object. */
export function buildSafetensorsView({ rawMeta, tensorCount, autoV2Hash }: SafetensorsViewInput): SafetensorsMetadata {
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

  return {
    tensorCount,
    raw: meta,
    lora,
    baseModel,
    training,
    dataset,
    modelSpec,
    outputName: meta['ss_output_name'],
    autoV2Hash,
  }
}

/**
 * Browser-local reader: parse a safetensors File object entirely in memory
 * (8-byte little-endian u64 header length, then the JSON header).
 */
export async function readLocalSafetensors(file: File): Promise<SafetensorsMetadata> {
  const lengthBytes = new DataView(await file.slice(0, 8).arrayBuffer())
  const headerLen = Number(lengthBytes.getBigUint64(0, true))
  if (headerLen === 0 || headerLen > MAX_HEADER_SIZE) {
    throw new Error(`Invalid header length: ${headerLen}`)
  }

  const headerJson = JSON.parse(
    new TextDecoder().decode(await file.slice(8, 8 + headerLen).arrayBuffer())
  ) as { __metadata__?: Record<string, string> }

  const tensorCount = Object.keys(headerJson).filter(k => k !== '__metadata__').length
  return buildSafetensorsView({ rawMeta: headerJson.__metadata__ ?? {}, tensorCount })
}
