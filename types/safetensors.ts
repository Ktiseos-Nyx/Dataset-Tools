export interface SafetensorsLora {
  networkModule?: unknown
  dim?: number
  alpha?: number
  networkArgs?: unknown
}

export interface SafetensorsBaseModel {
  name?: unknown
  hash?: unknown
  version?: unknown
  isV2?: boolean
}

export interface SafetensorsTraining {
  learningRate?: number
  unetLr?: number
  textEncoderLr?: number
  lrScheduler?: unknown
  lrWarmupSteps?: number
  epochs?: number
  epoch?: number
  steps?: number
  batchSize?: number
  gradientAccumulationSteps?: number
  mixedPrecision?: unknown
  fullFp16?: boolean
  maxGradNorm?: number
  optimizer?: unknown
  noiseOffset?: number
}

export interface SafetensorsDataset {
  numTrainImages?: number
  numRegImages?: number
  tagFrequency?: Record<string, Record<string, number>>
  datasetDirs?: unknown
}

export interface SafetensorsMetadata {
  tensorCount: number
  raw: Record<string, unknown>
  lora?: SafetensorsLora
  baseModel?: SafetensorsBaseModel
  training?: SafetensorsTraining
  dataset?: SafetensorsDataset
  modelSpec?: Record<string, unknown>
  outputName?: unknown
  autoV2Hash?: string
}
