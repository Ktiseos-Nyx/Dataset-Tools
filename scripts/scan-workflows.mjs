/**
 * Scans a folder of ComfyUI workflow JSONs and classifies every node type
 * against the ComfyUI-Manager extension-node-map. Reports which custom
 * packages each workflow needs. Caches the extension map for 6 hours.
 *
 * Usage: node scripts/scan-workflows.mjs "C:\path\to\workflows"
 */

import { readFileSync, writeFileSync, existsSync, readdirSync, statSync } from 'fs';
import { join, extname } from 'path';

const CACHE_PATH = new URL('../.cache/extension-node-map.json', import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1');
const CACHE_TTL_MS = 6 * 60 * 60 * 1000;
const EXTENSION_MAP_URL = 'https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/main/extension-node-map.json';

const BUILTIN_NODES = new Set([
  'KSampler','KSamplerAdvanced','KSamplerSelect','SamplerCustom','SamplerCustomAdvanced',
  'BasicScheduler','KarrasScheduler','ExponentialScheduler','SDTurboScheduler','BetaSamplingScheduler',
  'SplitSigmas','SplitSigmasDenoise','FlipSigmas',
  'CheckpointLoader','CheckpointLoaderSimple','UNETLoader','CLIPLoader','DualCLIPLoader','TripleCLIPLoader',
  'CLIPVisionLoader','ControlNetLoader','LoraLoader','LoraLoaderModelOnly','UpscaleModelLoader',
  'VAELoader','HypernetworkLoader','StyleModelLoader',
  'CLIPTextEncode','CLIPTextEncodeSDXL','CLIPTextEncodeSDXLRefiner','CLIPSetLastLayer','CLIPVisionEncode',
  'ConditioningCombine','ConditioningAverage','ConditioningConcat','ConditioningSetArea',
  'ConditioningSetMask','ConditioningSetTimestepRange','ConditioningZeroOut',
  'ControlNetApply','ControlNetApplyAdvanced','ControlNetApplySD3','FluxGuidance',
  'EmptyLatentImage','EmptySD3LatentImage','LatentUpscale','LatentUpscaleBy','LatentFromBatch',
  'LatentComposite','LatentCompositeMasked','LatentBlend','LatentCrop','RepeatLatentBatch',
  'LatentBatch','LatentAdd','LatentSubtract','LatentMultiply','LatentInterpolate',
  'LoadImage','LoadImageMask','SaveImage','PreviewImage',
  'ImageScale','ImageScaleBy','ImageScaleToTotalPixels','ImageUpscaleWithModel',
  'ImageInvert','ImageBatch','ImageCrop','ImagePadForOutpaint','ImageCompositeMasked',
  'ImageBlend','ImageBlur','ImageSharpen','ImageFromBatch','RebatchImages','RepeatImageBatch',
  'MaskToImage','ImageToMask','ImageColorToMask','SolidMask','InvertMask',
  'CropMask','MaskComposite','FeatherMask','GrowMask','ThresholdMask',
  'VAEDecode','VAEEncode','VAEEncodeForInpaint','VAEDecodeTiled','VAEEncodeTiled',
  'ModelMergeSimple','ModelMergeBlocks','ModelMergeSubtract','ModelMergeAdd',
  'FreeU','FreeU_V2','HyperTile','RescaleCFG','PerpNeg',
  'ModelSamplingDiscrete','ModelSamplingContinuousEDM','ModelSamplingFlux',
  'BasicGuider','CFGGuider','DualCFGGuider','DisableNoise','RandomNoise','AddNoise',
  'PrimitiveNode','Reroute','Note',
  'T5TextEncode','FluxTextEncode',
  'CheckpointSave','CLIPSave','VAESave',
  'SetUnionControlNetType',
]);

async function getExtensionMap() {
  if (existsSync(CACHE_PATH)) {
    const cached = JSON.parse(readFileSync(CACHE_PATH, 'utf8'));
    if (Date.now() - cached.fetchedAt < CACHE_TTL_MS) {
      console.log('Using cached extension map.\n');
      return cached.data;
    }
  }
  console.log('Fetching extension-node-map from ComfyUI-Manager...');
  const res = await fetch(EXTENSION_MAP_URL);
  if (!res.ok) throw new Error(`Failed to fetch extension map: ${res.status}`);
  const data = await res.json();
  writeFileSync(CACHE_PATH, JSON.stringify({ fetchedAt: Date.now(), data }, null, 2));
  console.log('Cached extension map.\n');
  return data;
}

function buildNodeIndex(extensionMap) {
  const index = new Map();
  for (const [repoUrl, [nodeList, meta]] of Object.entries(extensionMap)) {
    const title = meta?.title_aux || repoUrl.split('/').pop() || repoUrl;
    const repoName = repoUrl.replace('https://github.com/', '');
    for (const nodeType of (nodeList || [])) {
      if (!index.has(nodeType)) {
        index.set(nodeType, { repoUrl, repoName, title });
      }
    }
  }
  return index;
}

function findJsonFiles(dir) {
  const results = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      results.push(...findJsonFiles(full));
    } else if (extname(entry).toLowerCase() === '.json') {
      results.push(full);
    }
  }
  return results;
}

function classifyWorkflow(workflowPath, nodeIndex) {
  let workflow;
  try {
    workflow = JSON.parse(readFileSync(workflowPath, 'utf8'));
  } catch {
    return null;
  }

  const nodes = workflow.nodes || [];
  if (!nodes.length) return null;

  const customPackages = new Map(); // repoName → { title, nodes: Set }
  const unknownNodes = new Set();

  for (const node of nodes) {
    const type = node.type;
    if (!type || type === 'Note' || type === 'Reroute') continue;
    if (BUILTIN_NODES.has(type)) continue;

    const repo = nodeIndex.get(type);
    if (repo) {
      if (!customPackages.has(repo.repoName)) {
        customPackages.set(repo.repoName, { title: repo.title, nodes: new Set() });
      }
      customPackages.get(repo.repoName).nodes.add(type);
    } else {
      unknownNodes.add(type);
    }
  }

  return { nodeCount: nodes.length, customPackages, unknownNodes };
}

// ─── Main ────────────────────────────────────────────────────────────────────

const targetDir = process.argv[2];
if (!targetDir) {
  console.error('Usage: node scripts/scan-workflows.mjs "C:\\path\\to\\workflows"');
  process.exit(1);
}

const extensionMap = await getExtensionMap();
const nodeIndex = buildNodeIndex(extensionMap);

const jsonFiles = findJsonFiles(targetDir);
console.log(`Found ${jsonFiles.length} workflow JSON(s) in ${targetDir}\n`);
console.log('='.repeat(70));

for (const file of jsonFiles.sort()) {
  const result = classifyWorkflow(file, nodeIndex);
  if (!result) continue;

  const relPath = file.replace(targetDir, '').replace(/^[\\/]/, '');
  const { nodeCount, customPackages, unknownNodes } = result;

  console.log(`\n${relPath}`);
  console.log(`  Nodes: ${nodeCount} | Custom packages: ${customPackages.size} | Unknown nodes: ${unknownNodes.size}`);

  if (customPackages.size > 0) {
    console.log('  Packages:');
    for (const [repo, info] of [...customPackages.entries()].sort()) {
      console.log(`    - ${info.title} (${repo})`);
      for (const n of [...info.nodes].sort()) {
        console.log(`        ${n}`);
      }
    }
  }

  if (unknownNodes.size > 0) {
    console.log(`  Unknown (not in registry):`);
    for (const n of [...unknownNodes].sort()) {
      console.log(`    ? ${n}`);
    }
  }
}

console.log('\n' + '='.repeat(70));
console.log('Done.');
