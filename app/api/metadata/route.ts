import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';
import mime from 'mime-types';
// @ts-expect-error — exif-parser has no type declarations
import exifParser from 'exif-parser';
import iconv from 'iconv-lite';
import { classifyNodes, type NodeLookupResult } from '@/lib/comfyui-node-registry';

/**
 * Classify every class_type in a ComfyUI workflow against the extension-node-map
 * registry. GitHub fallback is intentionally disabled here — the panel triggers
 * it as a separate async request after the metadata response arrives, so the
 * initial load is never blocked by GitHub API latency.
 */
// Node provenance extracted from the Workflow PNG chunk (ComfyUI ≥1.26).
// Keys are class_type strings; values are the cnr_id / aux_id from node.properties.
type WorkflowProvenance = Record<string, { cnrId?: string; auxId?: string }>;

/**
 * Extract node provenance from the ComfyUI Workflow PNG chunk.
 * ComfyUI ≥1.26 stores cnr_id and aux_id in each node's properties:
 *   cnr_id: "comfy-core"        → built-in node
 *   aux_id: "owner/repo"        → custom node, GitHub repo
 * This is more authoritative than the extension-node-map registry and avoids
 * GitHub code-search false positives entirely.
 */
function extractWorkflowProvenance(workflowJson: string): WorkflowProvenance {
  const provenance: WorkflowProvenance = {};
  try {
    const wf = JSON.parse(workflowJson);
    const nodes: any[] = Array.isArray(wf.nodes) ? wf.nodes : [];
    for (const node of nodes) {
      const type = node?.type;
      const props = node?.properties ?? {};
      if (typeof type === 'string' && type && (props.cnr_id || props.aux_id)) {
        provenance[type] = { cnrId: props.cnr_id, auxId: props.aux_id };
      }
    }
  } catch {
    // Not valid JSON or unexpected shape — skip
  }
  return provenance;
}

async function classifyComfyUIWorkflow(
  workflow: Record<string, any>,
  provenance?: WorkflowProvenance,
): Promise<{
  summary: { total: number; builtin: number; custom: number; unknown: number; githubResolved: number };
  classifications: Record<string, NodeLookupResult>;
  unknownNodes: string[];
} | null> {
  const classTypes = new Set<string>();
  for (const node of Object.values(workflow)) {
    const ct = (node as any)?.class_type;
    if (typeof ct === 'string' && ct) classTypes.add(ct);
  }
  if (classTypes.size === 0) return null;

  let classifications: Record<string, NodeLookupResult>;
  try {
    classifications = await classifyNodes([...classTypes]);
  } catch (err) {
    console.error('[metadata] ComfyUI node classification failed:', err);
    classifications = {};
  }

  // Overlay Workflow-chunk provenance — this is authoritative and avoids
  // GitHub code-search false positives for nodes with known origins.
  if (provenance) {
    for (const ct of classTypes) {
      const p = provenance[ct];
      if (!p) continue;
      if (p.cnrId === 'comfy-core') {
        classifications[ct] = { classification: 'builtin' };
      } else if (p.auxId) {
        const repoTitle = p.auxId.split('/').pop() ?? p.auxId;
        classifications[ct] = {
          classification: 'custom',
          repo: {
            repoUrl: `https://github.com/${p.auxId}`,
            repoName: p.auxId,
            title: repoTitle,
          },
        };
      }
    }
  }

  let builtin = 0, custom = 0, unknown = 0, githubResolved = 0;
  const unknownNodes: string[] = [];
  for (const [ct, result] of Object.entries(classifications)) {
    switch (result.classification) {
      case 'builtin': builtin++; break;
      case 'custom':
        custom++;
        if (result.source === 'github') githubResolved++;
        break;
      case 'unknown': unknown++; unknownNodes.push(ct); break;
    }
  }

  return {
    summary: { total: classTypes.size, builtin, custom, unknown, githubResolved },
    classifications,
    unknownNodes,
  };
}

// PNG chunk parser for AI generation parameters
function parsePNGChunks(buffer: Buffer): Record<string, any> {
  const chunks: Record<string, any> = {};

  // Check PNG signature
  if (buffer.length < 8 || buffer.toString('hex', 0, 8) !== '89504e470d0a1a0a') {
    return chunks;
  }

  let offset = 8; // Skip PNG signature

  while (offset < buffer.length) {
    if (offset + 8 > buffer.length) break;

    const length = buffer.readUInt32BE(offset);
    const type = buffer.toString('ascii', offset + 4, offset + 8);

    if (offset + 12 + length > buffer.length) break;

    const data = buffer.slice(offset + 8, offset + 8 + length);

    // Parse text chunks
    if (type === 'tEXt') {
      const nullIndex = data.indexOf(0);
      if (nullIndex !== -1) {
        const key = data.toString('latin1', 0, nullIndex);
        const value = data.toString('utf8', nullIndex + 1);
        chunks[key] = value;
      }
    } else if (type === 'iTXt') {
      const nullIndex = data.indexOf(0);
      if (nullIndex !== -1) {
        const key = data.toString('latin1', 0, nullIndex);
        // Skip compression flag, compression method, language tag, translated keyword
        let textStart = nullIndex + 1;
        const compressionFlag = data[textStart++];
        const compressionMethod = data[textStart++];

        // Skip language tag (null-terminated)
        while (textStart < data.length && data[textStart] !== 0) textStart++;
        textStart++; // Skip null

        // Skip translated keyword (null-terminated)
        while (textStart < data.length && data[textStart] !== 0) textStart++;
        textStart++; // Skip null

        const value = data.toString('utf8', textStart);
        chunks[key] = value;
      }
    }

    offset += 12 + length; // length + type + data + CRC
  }

  return chunks;
}

// ============================================================================
// ComfyUI Workflow Extraction — Graph Trace Primary, Type Match Fallback
// ============================================================================

// Utility: is this value a node reference? (e.g. ["32", 0])
function isNodeRef(value: any): value is [string, number] {
  return Array.isArray(value) && value.length === 2 && typeof value[0] === 'string' && typeof value[1] === 'number';
}

// Utility: get a node from the workflow by ID
function getNode(workflow: Record<string, any>, id: string): any | null {
  const node = workflow[id];
  return (node && typeof node === 'object' && node.inputs) ? node : null;
}

// Utility: follow a node ref to its source node, with cycle detection
function followRef(workflow: Record<string, any>, ref: any, visited?: Set<string>): { nodeId: string; node: any } | null {
  if (!isNodeRef(ref)) return null;
  const seen = visited || new Set<string>();
  if (seen.has(ref[0])) return null;
  seen.add(ref[0]);
  const node = getNode(workflow, ref[0]);
  return node ? { nodeId: ref[0], node } : null;
}

// Common text input field names found across vanilla + custom ComfyUI nodes.
// Ordered roughly by frequency so the loop returns sooner on hot cases.
const TEXT_INPUT_KEYS = [
  'text', 'string', 'prompt', 'value',
  'text_a', 'text_b', 'text_g', 'text_l', 'text_c',
  // CLIPTextEncodeFlux fields (Flux architecture)
  'clip_l', 't5xxl',
  'positive', 'negative',
  'positive_prompt', 'negative_prompt',
  'user_prompt', 'wildcard_text', 'final_text',
  'populated_text', 'output_text',
] as const;

// Field-name fragments that disqualify a value from being treated as prompt text.
const NON_PROMPT_KEY_FRAGMENTS = ['name', 'file', 'path', 'method', 'mode', 'type', 'format'];

function isPromptyKey(key: string): boolean {
  const lower = key.toLowerCase();
  return !NON_PROMPT_KEY_FRAGMENTS.some(f => lower.includes(f));
}

// Find a text/prompt string in a node's inputs.
// Strategy: try known keys first, then scan all string fields.
// `hint` can be "positive" or "negative" to prefer matching fields.
function findText(workflow: Record<string, any>, node: any, visited?: Set<string>, hint?: string): string | null {
  const inputs = node.inputs || {};

  // Priority 1: if hint is given, look for fields containing that hint
  // (e.g. "POSITIVE_PROMPT", "negative_prompt", "positive", "negative")
  if (hint) {
    const hintUpper = hint.toUpperCase();
    for (const [key, val] of Object.entries(inputs)) {
      const keyUpper = key.toUpperCase();
      if (keyUpper.includes(hintUpper) &&
          (keyUpper.includes('PROMPT') || keyUpper.includes('TEXT') || keyUpper.includes('STRING'))) {
        if (typeof val === 'string' && val.trim()) return val;
        if (isNodeRef(val)) {
          const upstream = followRef(workflow, val, visited);
          if (upstream) {
            const text = findText(workflow, upstream.node, visited, hint);
            if (text) return text;
          }
        }
      }
    }
    // Also check just the hint name directly (e.g. inputs.positive, inputs.negative)
    if (typeof inputs[hint] === 'string' && inputs[hint].trim()) return inputs[hint];
    if (isNodeRef(inputs[hint])) {
      const upstream = followRef(workflow, inputs[hint], visited);
      if (upstream) {
        const text = findText(workflow, upstream.node, visited, hint);
        if (text) return text;
      }
    }
  }

  // Priority 2: known common text field names
  for (const key of TEXT_INPUT_KEYS) {
    if (typeof inputs[key] === 'string' && inputs[key].trim()) return inputs[key];
    if (isNodeRef(inputs[key])) {
      const upstream = followRef(workflow, inputs[key], visited);
      if (upstream) {
        const text = findText(workflow, upstream.node, visited, hint);
        if (text) return text;
      }
    }
  }

  // Priority 3: any NodeRef input — follow it. This catches custom routers
  // that store the prompt under a non-standard key (e.g. `wildcard`, `seed_text`).
  for (const [key, val] of Object.entries(inputs)) {
    if (!isPromptyKey(key)) continue;
    if (isNodeRef(val)) {
      const upstream = followRef(workflow, val, visited);
      if (upstream) {
        const text = findText(workflow, upstream.node, visited, hint);
        if (text) return text;
      }
    }
  }

  // Priority 4: scan all string inputs that look like prompts (longer than ~10 chars,
  // not a filename or simple config value)
  let bestText: string | null = null;
  for (const [key, val] of Object.entries(inputs)) {
    if (typeof val === 'string' && val.trim().length > 10) {
      if (!isPromptyKey(key)) continue;
      if (!bestText || val.length > bestText.length) bestText = val;
    }
  }
  if (bestText) return bestText;

  return null;
}

// Quadmoon-style recursive prompt extraction. Walks back through every
// string-typed connection and joins the text contributions with " | ", which
// preserves both branches of ConditioningCombine and similar combiner nodes.
//
// Returns null when nothing prompt-shaped is reachable. Otherwise returns the
// combined text in upstream-first order so the most-specific source ends up
// at the front (matches Python's collected_texts ordering).
function extractPromptTextWithTrace(
  workflow: Record<string, any>,
  startNodeId: string,
  hint?: string,
  maxDepth: number = 10,
  skipNodes?: Set<string>,
): string | null {
  const seen = new Set<string>();
  const collected: string[] = [];

  function visit(nodeId: string, depth: number) {
    if (depth > maxDepth || seen.has(nodeId)) return;
    if (skipNodes?.has(nodeId)) return;
    seen.add(nodeId);

    const node = getNode(workflow, nodeId);
    if (!node) return;
    const inputs = node.inputs || {};

    // First recurse into upstream nodes via NodeRef inputs. We follow every
    // ref (not just text-shaped ones) because conditioning combiners route
    // through CONDITIONING-typed inputs that still feed text underneath.
    for (const [key, val] of Object.entries(inputs)) {
      if (!isNodeRef(val)) continue;
      // Skip clearly non-text plumbing so we don't drag in seeds/clip/vae paths.
      const lower = key.toLowerCase();
      if (
        lower === 'clip' || lower === 'vae' || lower === 'model' || lower === 'image' ||
        lower === 'latent' || lower === 'mask' || lower === 'samples' || lower === 'sigmas' ||
        lower === 'noise' || lower === 'guider' || lower === 'sampler' || lower === 'scheduler'
      ) {
        continue;
      }
      visit((val as [string, number])[0], depth + 1);
    }

    // Then collect any direct text on this node.
    const direct = findText(workflow, node, undefined, hint);
    if (direct && !collected.includes(direct)) {
      collected.push(direct);
    }
  }

  visit(startNodeId, 0);

  if (collected.length === 0) return null;
  // Upstream-first ordering reads more naturally for combiner chains.
  return collected.length === 1 ? collected[0] : collected.reverse().join(' | ');
}

// ---- Field-based node identification (no type names needed) ----
function hasFields(inputs: any, ...fields: string[]): boolean {
  return fields.every(f => inputs[f] !== undefined);
}

function isSamplerByFields(inputs: any): boolean {
  // Standard KSampler / FSamplerAdvanced: has steps/cfg/sampler_name/seed/positive/negative
  const samplerFields = ['steps', 'cfg', 'sampler_name', 'seed', 'positive', 'negative'];
  const matched = samplerFields.filter(f => inputs[f] !== undefined);
  if (matched.length >= 3) return true;
  // SamplerCustomAdvanced (Flux composite sampler) — all connections are node refs.
  // Identified by having guider + sigmas + noise all as node refs (its 3 defining wires).
  return ['guider', 'sigmas', 'noise'].every(f => isNodeRef(inputs[f]));
}

function isCheckpointByFields(inputs: any): boolean {
  return !!inputs.ckpt_name;
}

function isLatentByFields(inputs: any): boolean {
  return hasFields(inputs, 'width', 'height', 'batch_size');
}

function extractComfyUIParams(
  workflow: Record<string, any>,
  classifications: Record<string, NodeLookupResult> = {},
): Record<string, any> {
  const extracted: Record<string, any> = {};

  // Type-match fallback helper (for platforms that wrap standard nodes)
  const typeMatches = (classType: string, ...patterns: string[]) =>
    patterns.some(p => classType.includes(p));

  // Classification helper: is this class_type a recognised node?
  // Anything in the registry (builtin OR custom-via-extension-map OR custom-via-github)
  // is "known" — meaning we can apply field-based heuristics with more confidence.
  const isKnownNode = (classType: string): boolean => {
    const result = classifications[classType];
    return result !== undefined && result.classification !== 'unknown';
  };

  // ========================================================================
  // PRE-PASS: Identify muted/bypassed nodes and AI prompt enhancers
  // ComfyUI mode: 0 = normal, 2 = muted, 4 = bypassed
  // ========================================================================
  const mutedNodeIds = new Set<string>();
  const aiPromptEnhancers: Array<{ nodeId: string; classType: string; reason: string }> = [];

  const AI_ENHANCER_PATTERNS = [
    'llm', 'gpt', 'claude', 'deepseek', 'ollama', 'llama', 'mistral',
    'gemini', 'qwen', 'prompt enhance', 'prompt expand', 'prompt refine',
    'prompt improve', 'prompt writer', 'prompt generator', 'ai prompt',
  ];

  for (const [nodeId, nodeData] of Object.entries(workflow)) {
    const node = nodeData as any;
    if (!node?.inputs) continue;

    // Filter muted/bypassed nodes
    if (node.mode === 2 || node.mode === 4) {
      mutedNodeIds.add(nodeId);
      continue;
    }

    // Detect AI prompt enhancement nodes
    const ct = (node.class_type || '').toLowerCase();
    for (const pattern of AI_ENHANCER_PATTERNS) {
      if (ct.includes(pattern)) {
        aiPromptEnhancers.push({ nodeId, classType: node.class_type, reason: `class_type contains '${pattern}'` });
        break;
      }
    }
  }

  if (aiPromptEnhancers.length > 0) {
    extracted.ai_prompt_enhancement = true;
    extracted.ai_prompt_enhancers = aiPromptEnhancers.map(e => `${e.classType} (node ${e.nodeId})`);
  }

  // ========================================================================
  // PHASE 1: Field-based scan (type-agnostic)
  // Identify nodes by what data they carry, not what they're called
  // ========================================================================
  const samplerNodes: { id: string; node: any }[] = [];
  const loraNodes: { id: string; node: any }[] = [];

  for (const [nodeId, nodeData] of Object.entries(workflow)) {
    const node = nodeData as any;
    if (!node?.inputs || mutedNodeIds.has(nodeId)) continue;
    const inputs = node.inputs;
    const classType = node.class_type || '';

    // --- Sampler: identified by having steps + cfg + positive/negative ---
    if (isSamplerByFields(inputs)) {
      samplerNodes.push({ id: nodeId, node });
    }

    // --- Checkpoint: identified by having ckpt_name ---
    if (isCheckpointByFields(inputs)) {
      extracted.model = inputs.ckpt_name;
    }

    // --- UNET loader: identified by unet_name ---
    if (inputs.unet_name && !extracted.model) {
      extracted.model = inputs.unet_name;
    }

    // --- Latent image: identified by width + height + batch_size ---
    // Also handles combo loaders with empty_latent_width/empty_latent_height
    if (isLatentByFields(inputs)) {
      const w = inputs.width, h = inputs.height;
      if (typeof w === 'number' && typeof h === 'number') {
        extracted.size = `${w}x${h}`;
      }
    }
    if (!extracted.size && inputs.empty_latent_width && inputs.empty_latent_height) {
      const w = inputs.empty_latent_width, h = inputs.empty_latent_height;
      if (typeof w === 'number' && typeof h === 'number') {
        extracted.size = `${w}x${h}`;
      }
    }

    // --- VAE: identified by vae_name ---
    if (inputs.vae_name && !extracted.vae) {
      extracted.vae = inputs.vae_name;
    }

    // --- CLIP skip: identified by stop_at_clip_layer or clip_skip ---
    if (inputs.stop_at_clip_layer) {
      extracted.clip_skip = String(Math.abs(inputs.stop_at_clip_layer));
    }
    if (inputs.clip_skip && !extracted.clip_skip) {
      extracted.clip_skip = String(Math.abs(inputs.clip_skip));
    }

    // --- LoRA: identified by lora_name, numbered lora_name_N, or <lora:...> tags ---
    if (inputs.lora_name && inputs.lora_name !== 'None') {
      loraNodes.push({ id: nodeId, node });
    }
    // LoRA Stacker nodes use numbered fields: lora_name_1, lora_name_2, etc.
    for (const [key, val] of Object.entries(inputs)) {
      if (/^lora_name_\d+$/.test(key) && typeof val === 'string' && val !== 'None') {
        loraNodes.push({ id: nodeId, node });
        break; // Only push once per node
      }
    }
    // Power Lora Loader (rgthree) uses lora_1, lora_2, ... object fields: {on, lora, strength}
    for (const [key, val] of Object.entries(inputs)) {
      if (/^lora_\d+$/.test(key) && val !== null && typeof val === 'object' && (val as any).lora) {
        loraNodes.push({ id: nodeId, node });
        break;
      }
    }
    if (typeof inputs.text === 'string' && inputs.text.includes('<lora:')) {
      loraNodes.push({ id: nodeId, node });
    }
  }

  // Extract LoRAs
  const loraSet = new Set<string>();
  for (const { node } of loraNodes) {
    const inputs = node.inputs || {};
    if (inputs.lora_name && inputs.lora_name !== 'None') {
      loraSet.add(inputs.lora_name);
    }
    // Handle numbered LoRA stacker fields (lora_name_1, lora_wt_1, model_weight_1 etc.)
    for (const [key, val] of Object.entries(inputs)) {
      const numMatch = key.match(/^lora_name_(\d+)$/);
      if (numMatch && typeof val === 'string' && val !== 'None') {
        const n = numMatch[1];
        // Skip disabled loras (CR LoRA Stack uses switch_N: "On"/"Off")
        const switchVal = inputs[`switch_${n}`];
        if (typeof switchVal === 'string' && switchVal.toLowerCase() === 'off') continue;
        // Weight may be lora_wt_N (generic stacker) or model_weight_N (CR LoRA Stack)
        const weight = inputs[`lora_wt_${n}`] ?? inputs[`model_weight_${n}`];
        if (typeof weight === 'number') {
          loraSet.add(`${val} (${weight})`);
        } else {
          loraSet.add(val);
        }
      }
    }
    // Power Lora Loader (rgthree) — lora_N object fields, only include enabled loras
    for (const [key, val] of Object.entries(inputs)) {
      if (/^lora_\d+$/.test(key) && val !== null && typeof val === 'object') {
        const loraObj = val as any;
        if (loraObj.on && typeof loraObj.lora === 'string' && loraObj.lora !== 'None') {
          const strength = typeof loraObj.strength === 'number' ? ` (${loraObj.strength})` : '';
          loraSet.add(`${loraObj.lora}${strength}`);
        }
      }
    }
    if (typeof inputs.text === 'string') {
      const matches = inputs.text.matchAll(/<lora:([^:>]+):([^>]+)>/g);
      for (const m of matches) loraSet.add(`${m[1]} (${m[2]})`);
    }
  }
  if (loraSet.size > 0) extracted.loras = [...loraSet];

  // ========================================================================
  // PHASE 2: Graph trace from sampler nodes
  // Follow positive/negative wires backwards to find prompt text
  // ========================================================================
  if (samplerNodes.length > 0) {
    // Use the first sampler that has the most complete inputs (most likely the "main" one)
    // Prefer samplers with denoise=1 or no denoise (full generation, not inpainting/refine)
    const mainSampler = samplerNodes.find(s => {
      const d = s.node.inputs.denoise;
      return d === undefined || d === 1;
    }) || samplerNodes[0];

    const inputs = mainSampler.node.inputs;

    // Extract sampler settings
    if (inputs.steps) extracted.steps = String(inputs.steps);
    if (inputs.cfg) extracted.cfg_scale = String(inputs.cfg);
    // sampler_name is the standard KSampler field; custom samplers (FSamplerAdvanced
    // etc.) use 'sampler' instead. Fall back to 'sampler' when sampler_name is absent.
    if (inputs.sampler_name) extracted.sampler = inputs.sampler_name;
    else if (typeof inputs.sampler === 'string') extracted.sampler = inputs.sampler;
    if (inputs.scheduler) extracted.scheduler = inputs.scheduler;
    if (inputs.denoise !== undefined && inputs.denoise !== 1) {
      extracted.denoise = String(inputs.denoise);
    }

    // Resolve seed (might be a ref to a seed generator node)
    for (const seedKey of ['seed', 'noise_seed']) {
      if (inputs[seedKey] !== undefined) {
        if (typeof inputs[seedKey] === 'number') {
          extracted.seed = String(inputs[seedKey]);
          break;
        }
        // Follow ref for seed
        const seedSource = followRef(workflow, inputs[seedKey]);
        if (seedSource) {
          for (const val of Object.values(seedSource.node.inputs || {})) {
            if (typeof val === 'number' && val > 1000) { // seeds are large numbers
              extracted.seed = String(val);
              break;
            }
          }
        }
        if (extracted.seed) break;
      }
    }

    // --- SamplerCustomAdvanced: follow specialised input refs ---
    // This Flux-era node delegates to BasicScheduler (steps/scheduler),
    // KSamplerSelect (sampler_name), RandomNoise (noise_seed), and BasicGuider
    // (positive conditioning). All connections are node refs, not direct values.
    if (isNodeRef(inputs.sigmas)) {
      const schedNode = followRef(workflow, inputs.sigmas);
      if (schedNode?.node.inputs) {
        const si = schedNode.node.inputs;
        if (!extracted.steps && si.steps !== undefined) extracted.steps = String(si.steps);
        if (!extracted.scheduler && si.scheduler) extracted.scheduler = si.scheduler;
        if (!extracted.denoise && si.denoise !== undefined && si.denoise !== 1) {
          extracted.denoise = String(si.denoise);
        }
      }
    }
    if (!extracted.sampler && isNodeRef(inputs.sampler)) {
      const kselectNode = followRef(workflow, inputs.sampler);
      if (kselectNode?.node.inputs?.sampler_name) {
        extracted.sampler = kselectNode.node.inputs.sampler_name;
      }
    }
    if (!extracted.seed && isNodeRef(inputs.noise)) {
      const noiseNode = followRef(workflow, inputs.noise);
      if (noiseNode?.node.inputs) {
        const noiseSeed = noiseNode.node.inputs.noise_seed ?? noiseNode.node.inputs.seed;
        if (typeof noiseSeed === 'number') extracted.seed = String(noiseSeed);
      }
    }

    // --- Trace positive conditioning wire ---
    // Quadmoon's _extract_prompt_text_with_trace handles combiners (multiple
    // CLIPTextEncodes via ConditioningCombine) by joining all contributions.
    if (isNodeRef(inputs.positive)) {
      const startId = (inputs.positive as [string, number])[0];
      const traced = extractPromptTextWithTrace(workflow, startId, 'positive', 10, mutedNodeIds);
      if (traced) extracted.prompt = traced;
    }
    // SamplerCustomAdvanced uses a guider node instead of direct positive/negative wires
    if (!extracted.prompt && isNodeRef(inputs.guider)) {
      const guiderNode = followRef(workflow, inputs.guider);
      if (guiderNode && isNodeRef(guiderNode.node.inputs?.conditioning)) {
        const condId = (guiderNode.node.inputs.conditioning as [string, number])[0];
        const traced = extractPromptTextWithTrace(workflow, condId, 'positive', 10, mutedNodeIds);
        if (traced) extracted.prompt = traced;
      }
    }

    // --- Trace negative conditioning wire ---
    if (isNodeRef(inputs.negative)) {
      const startId = (inputs.negative as [string, number])[0];
      const traced = extractPromptTextWithTrace(workflow, startId, 'negative', 10, mutedNodeIds);
      if (traced) extracted.negative_prompt = traced;
    }
  }

  // ========================================================================
  // PHASE 3: Type-match fallback (registry-aware)
  // If graph tracing didn't find prompts, scan for text encoder candidates.
  // We use the registry classification to expand the candidate set: any node
  // that's known (builtin OR custom-via-registry) and carries a text-shaped
  // input is a plausible text encoder, even if its class_type doesn't match
  // the hardcoded CLIPTextEncode/T5/Flux patterns.
  // ========================================================================
  if (!extracted.prompt) {
    const promptTexts: { text: string; nodeId: string }[] = [];

    // Field shapes that strongly suggest a text encoder node
    const TEXT_ENCODER_FIELD_HINTS = ['text', 'text_g', 'text_l', 'prompt', 'string'];
    const looksLikeTextEncoder = (inputs: Record<string, any>, classType: string): boolean => {
      // Hardcoded patterns first (handles workflows with no registry classification)
      if (typeMatches(classType, 'CLIPTextEncode', 'T5TextEncode', 'FluxTextEncode',
                                  'TextEncode', 'PromptEncode')) {
        return true;
      }
      // Class-name heuristics on lowercased name
      const ctLower = classType.toLowerCase();
      if (ctLower.includes('encode') && (ctLower.includes('text') || ctLower.includes('prompt') || ctLower.includes('clip'))) {
        return true;
      }
      // Registry-aware: if this is a known custom node carrying a text-shaped input
      if (isKnownNode(classType)) {
        for (const field of TEXT_ENCODER_FIELD_HINTS) {
          const v = inputs[field];
          if (typeof v === 'string' && v.trim().length > 0) return true;
        }
      }
      return false;
    };

    for (const [nodeId, nodeData] of Object.entries(workflow)) {
      const node = nodeData as any;
      const classType = node.class_type || '';
      const inputs = node.inputs || {};
      if (mutedNodeIds.has(nodeId)) continue;

      if (looksLikeTextEncoder(inputs, classType)) {
        const text = findText(workflow, node);
        if (text) promptTexts.push({ text, nodeId });
      }
    }

    if (promptTexts.length > 0) {
      // Try to sort positive vs negative using sampler wiring
      const negativeNodeIds = new Set<string>();
      for (const s of samplerNodes) {
        const neg = s.node.inputs?.negative;
        if (isNodeRef(neg)) {
          negativeNodeIds.add(neg[0]);
          // Follow one more level
          const condNode = getNode(workflow, neg[0]);
          if (condNode) {
            for (const val of Object.values(condNode.inputs || {})) {
              if (isNodeRef(val)) negativeNodeIds.add(val[0]);
            }
          }
        }
      }

      for (const pt of promptTexts) {
        if (negativeNodeIds.has(pt.nodeId)) {
          if (!extracted.negative_prompt) extracted.negative_prompt = pt.text;
        } else if (!extracted.prompt || pt.text.length > extracted.prompt.length) {
          extracted.prompt = pt.text;
        }
      }

      // Last resort: longest = positive, next = negative
      if (!extracted.prompt) {
        promptTexts.sort((a, b) => b.text.length - a.text.length);
        extracted.prompt = promptTexts[0].text;
        if (promptTexts.length > 1) extracted.negative_prompt = promptTexts[1].text;
      }
    }
  }

  // ========================================================================
  // PHASE 4: ControlNet detection
  // ========================================================================
  for (const [nodeId, nodeData] of Object.entries(workflow)) {
    const node = nodeData as any;
    if (mutedNodeIds.has(nodeId)) continue;
    const ct = (node.class_type || '').toLowerCase();
    if (ct.includes('controlnet') || ct.includes('control_net')) {
      extracted.uses_controlnet = true;
      break;
    }
  }

  // ========================================================================
  // PHASE 5: Forward conditioning trace (when backward trace was ambiguous)
  // Walk from text-encoder nodes forward through the graph to see if they
  // connect to a sampler's positive or negative input.
  // ========================================================================
  if (extracted.prompt && !extracted.negative_prompt && samplerNodes.length > 0) {
    // Build a forward adjacency: for each node, track which nodes reference it
    const forwardEdges: Record<string, Array<{ targetId: string; inputName: string }>> = {};
    for (const [nodeId, nodeData] of Object.entries(workflow)) {
      const node = nodeData as any;
      if (!node?.inputs || mutedNodeIds.has(nodeId)) continue;
      for (const [inputName, val] of Object.entries(node.inputs)) {
        if (isNodeRef(val)) {
          const sourceId = (val as [string, number])[0];
          if (!forwardEdges[sourceId]) forwardEdges[sourceId] = [];
          forwardEdges[sourceId].push({ targetId: nodeId, inputName });
        }
      }
    }

    // For each text-encoding node, trace forward to see if it eventually
    // connects to a sampler's negative input
    for (const [nodeId, nodeData] of Object.entries(workflow)) {
      const node = nodeData as any;
      if (mutedNodeIds.has(nodeId)) continue;
      const ct = node.class_type || '';
      if (!typeMatches(ct, 'CLIPTextEncode', 'T5TextEncode', 'FluxTextEncode')) continue;

      const text = findText(workflow, node);
      if (!text || text === extracted.prompt) continue;

      // Walk forward up to 5 hops to see if we reach a sampler negative input
      const visited = new Set<string>();
      const queue: string[] = [nodeId];
      let isNegative = false;

      for (let depth = 0; depth < 5 && queue.length > 0 && !isNegative; depth++) {
        const nextQueue: string[] = [];
        for (const current of queue) {
          if (visited.has(current)) continue;
          visited.add(current);
          for (const edge of (forwardEdges[current] || [])) {
            const targetNode = workflow[edge.targetId] as any;
            if (!targetNode?.inputs) continue;
            // Check if target is a sampler and input is 'negative'
            if (isSamplerByFields(targetNode.inputs) && edge.inputName === 'negative') {
              isNegative = true;
              break;
            }
            // Check for guider nodes connecting to negative
            const targetCt = (targetNode.class_type || '').toLowerCase();
            if ((targetCt.includes('guider') || targetCt.includes('guidance')) &&
                edge.inputName.toLowerCase().includes('negative')) {
              isNegative = true;
              break;
            }
            nextQueue.push(edge.targetId);
          }
          if (isNegative) break;
        }
        queue.length = 0;
        queue.push(...nextQueue);
      }

      if (isNegative && text) {
        extracted.negative_prompt = text;
        break; // Found it
      }
    }
  }

  return extracted;
}

/**
 * Coerce any JSON-derived value to a plain string suitable for rendering.
 * Some metadata formats (e.g. NovelAI v3 reference images, Draw Things style
 * objects) store fields like `prompt` as `{ content, image, ... }` objects
 * instead of plain strings — passing these straight to React triggers error
 * #31. We unwrap known shapes and stringify everything else.
 */
function coercePromptValue(val: unknown): string | undefined {
  if (val === null || val === undefined) return undefined;
  if (typeof val === 'string') return val;
  if (typeof val === 'number' || typeof val === 'boolean' || typeof val === 'bigint') return String(val);
  if (Array.isArray(val)) {
    const parts = val.map(coercePromptValue).filter((s): s is string => !!s);
    return parts.length > 0 ? parts.join(', ') : undefined;
  }
  if (typeof val === 'object') {
    const obj = val as Record<string, unknown>;
    // Common nested-text shapes seen in the wild
    for (const key of ['content', 'text', 'prompt', 'caption', 'value', 'description']) {
      if (typeof obj[key] === 'string') return obj[key] as string;
    }
    // Last resort: pretty JSON so the user at least sees something useful
    try {
      return JSON.stringify(val);
    } catch {
      return undefined;
    }
  }
  return undefined;
}

// TensorArt-specific ComfyUI node class_types
const TENSORART_NODE_TYPES = new Set([
  'ECHOCheckpointLoaderSimple', 'TensorArt_CheckpointLoader',
  'TensorArt_PromptText', 'KolorsCheckpointLoaderSimple', 'TensorArtLoadChatGLM3',
]);

// Parse AI generation parameters from various formats
async function parseAIMetadata(chunks: Record<string, any>): Promise<Record<string, any>> {
  const aiData: Record<string, any> = {};

  // --- InvokeAI: dedicated invokeai_metadata PNG chunk ---
  if (chunks.invokeai_metadata) {
    try {
      const inv = JSON.parse(chunks.invokeai_metadata);
      if (inv.positive_prompt !== undefined) {
        aiData.workflow_type = 'InvokeAI';
        if (inv.positive_prompt) aiData.prompt = String(inv.positive_prompt);
        if (inv.negative_prompt) aiData.negative_prompt = String(inv.negative_prompt);
        if (inv.seed !== undefined) aiData.seed = String(inv.seed);
        if (inv.steps !== undefined) aiData.steps = String(inv.steps);
        if (inv.cfg_scale !== undefined) aiData.cfg_scale = String(inv.cfg_scale);
        if (inv.scheduler) aiData.scheduler = String(inv.scheduler);
        if (inv.model?.name) aiData.model = String(inv.model.name);
        if (inv.width && inv.height) aiData.size = `${inv.width}x${inv.height}`;
      }
    } catch { /* not JSON */ }
  }

  // --- LibLibAI: AIGC PNG chunk containing the liblibai.com service string ---
  if (!aiData.workflow_type && typeof chunks.AIGC === 'string' && chunks.AIGC.includes('liblibai.com')) {
    aiData.workflow_type = 'LibLibAI';
    const cidMatch = chunks.AIGC.match(/'ContentID':\s*(\d+)/);
    if (cidMatch) aiData.content_id = cidMatch[1];
  }

  // --- A1111-family + JSON-format parameters (parameters PNG chunk / EXIF text) ---
  // Some tools (smZ CLIPTextEncode, etc.) write 'Parameters' with a capital P
  const parametersChunk = chunks.parameters ?? chunks.Parameters;
  if (!aiData.workflow_type && parametersChunk) {
    const params = String(parametersChunk);

    // JSON-format parameters: SwarmUI and EasyDiffusion embed JSON here
    if (params.trim().startsWith('{')) {
      try {
        const jp = JSON.parse(params);
        // SwarmUI: has comfyuisampler / autowebuisampler / cfgscale (not a raw ComfyUI node)
        if ((jp.comfyuisampler !== undefined || jp.autowebuisampler !== undefined || jp.cfgscale !== undefined) && !jp.class_type) {
          const sd = jp.sui_image_params ?? jp;
          aiData.workflow_type = 'SwarmUI';
          if (sd.prompt) aiData.prompt = String(sd.prompt);
          if (sd.negativeprompt) aiData.negative_prompt = String(sd.negativeprompt);
          if (sd.seed !== undefined) aiData.seed = String(sd.seed);
          if (sd.steps !== undefined) aiData.steps = String(sd.steps);
          if (sd.cfgscale !== undefined) aiData.cfg_scale = String(sd.cfgscale);
          if (sd.width && sd.height) aiData.size = `${sd.width}x${sd.height}`;
          if (sd.model) aiData.model = String(sd.model);
          const swarmSampler = sd.comfyuisampler ?? sd.autowebuisampler;
          if (swarmSampler) aiData.sampler = String(swarmSampler);
        // EasyDiffusion: uses verbose field name num_inference_steps instead of steps
        } else if (jp.num_inference_steps !== undefined) {
          aiData.workflow_type = 'EasyDiffusion';
          const edPrompt = jp.prompt ?? jp.Prompt;
          if (edPrompt) aiData.prompt = String(edPrompt);
          const edNeg = jp.negative_prompt ?? jp['Negative Prompt'] ?? jp.negative;
          if (edNeg) aiData.negative_prompt = String(edNeg);
          aiData.steps = String(jp.num_inference_steps);
          if (jp.guidance_scale !== undefined) aiData.cfg_scale = String(jp.guidance_scale);
          if (jp.seed !== undefined) aiData.seed = String(jp.seed);
          const edSampler = jp.sampler_name ?? jp.sampler;
          if (edSampler) aiData.sampler = String(edSampler);
          if (jp.width && jp.height) aiData.size = `${jp.width}x${jp.height}`;
          if (jp.use_stable_diffusion_model) {
            const mp = String(jp.use_stable_diffusion_model);
            aiData.model = mp.split(/[/\\]/).pop()?.replace(/\.(safetensors|ckpt|pt)$/i, '') ?? mp;
          }
        }
      } catch { /* not JSON, fall through to A1111 text parsing */ }
    }

    // A1111-style text parameters (A1111, Forge, Yodayo, Civitai A1111)
    if (!aiData.workflow_type) {
      // Extract positive prompt (everything before "Negative prompt:")
      const negativeMatch = params.match(/Negative prompt:\s*([\s\S]+?)(?:\n|$)/);
      const splitIndex = params.indexOf('\nNegative prompt:');

      if (splitIndex !== -1) {
        aiData.prompt = params.substring(0, splitIndex).trim();
        if (negativeMatch) {
          aiData.negative_prompt = negativeMatch[1].split('\n')[0].trim();
        }
      } else {
        aiData.prompt = params.split('\n')[0].trim();
      }

      // Extract generation settings (last line typically carries key=value pairs)
      const lines = params.split('\n');
      const settingsLine = lines[lines.length - 1];

      const stepMatch = settingsLine.match(/Steps:\s*(\d+)/);
      const samplerMatch = settingsLine.match(/Sampler:\s*([^,]+)/);
      const cfgMatch = settingsLine.match(/CFG scale:\s*([\d.]+)/);
      const seedMatch = settingsLine.match(/Seed:\s*(\d+)/);
      const sizeMatch = settingsLine.match(/Size:\s*(\d+x\d+)/);
      const modelMatch = settingsLine.match(/Model:\s*([^,]+)/);

      if (stepMatch) aiData.steps = stepMatch[1];
      if (samplerMatch) aiData.sampler = samplerMatch[1].trim();
      if (cfgMatch) aiData.cfg_scale = cfgMatch[1];
      if (seedMatch) aiData.seed = seedMatch[1];
      if (sizeMatch) aiData.size = sizeMatch[1];
      if (modelMatch) aiData.model = modelMatch[1].trim();

      // Version field (search all lines, not just the last — extensions add extra lines)
      const versionMatch = params.match(/Version:\s*([^,\n]+)/);
      const versionStr = versionMatch ? versionMatch[1].trim() : '';
      if (versionStr) aiData.version = versionStr;

      // Platform detection — most-specific signal wins
      if (params.includes('NGMS:')) {
        // Yodayo/Moescape: NGMS is their unique content-filter strength field
        aiData.workflow_type = 'Yodayo';
        const ngmsMatch = params.match(/NGMS:\s*([\d.]+)/);
        if (ngmsMatch) aiData.ngms = ngmsMatch[1];
      } else if (/Civitai resources:|Civitai metadata:/.test(params)) {
        // Civitai on-site generator embeds explicit resource metadata
        aiData.workflow_type = 'Civitai';
      } else if (/^f\d/i.test(versionStr)) {
        // Forge: version string starts with 'f' (e.g. "f0.0.17-dirty-1254-gabcdef")
        aiData.workflow_type = 'Forge';
      } else if (versionStr.toLowerCase() === 'comfyui') {
        // smZ CLIPTextEncode and similar ComfyUI nodes that emit A1111-style params
        // include "Version: ComfyUI" to signal they're ComfyUI-generated
        aiData.workflow_type = 'ComfyUI';
      } else {
        aiData.workflow_type = 'AUTOMATIC1111';
      }
    }
  }

  // --- ComfyUI format: JSON workflow stored in "prompt" PNG chunk ---
  if (chunks.prompt) {
    try {
      // Sanitize NaN/Infinity values that break JSON.parse
      const sanitized = chunks.prompt
        .replace(/:\s*NaN/g, ': null')
        .replace(/:\s*Infinity/g, ': null')
        .replace(/:\s*-Infinity/g, ': null');

      const workflow = JSON.parse(sanitized);
      aiData.comfy_workflow = chunks.workflow ? JSON.parse(chunks.workflow) : workflow;
      // Default to ComfyUI; override with service-specific signals below
      aiData.workflow_type = 'ComfyUI';

      // UUID pattern used by ArcEnCiel for lora names and SaveImage prefixes
      const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

      for (const nodeData of Object.values(workflow)) {
        const node = nodeData as any;
        const inputs = node?.inputs ?? {};

        // TensorArt: proprietary node class_types or EMS-<id> model naming
        if (TENSORART_NODE_TYPES.has(node?.class_type)) { aiData.workflow_type = 'TensorArt'; break; }
        const ckpt = inputs.ckpt_name;
        if (typeof ckpt === 'string' && /EMS-\d+/i.test(ckpt)) { aiData.workflow_type = 'TensorArt'; break; }

        // ArcEnCiel: SaveImage prefix is "generator/{uuid}", and/or lora names
        // are UUID-prefixed (e.g. "ab234327-..._LoraName.safetensors").
        // ArcEnCiel runs standard ComfyUI nodes so there are no proprietary class_types.
        // NOTE: no API integration yet — pending contact with the ArcEnCiel team.
        if (node?.class_type === 'SaveImage') {
          const prefix = inputs.filename_prefix;
          if (typeof prefix === 'string' && /^generator\/[0-9a-f-]{36}$/i.test(prefix)) {
            aiData.workflow_type = 'ArcEnCiel';
          }
        }
        if (aiData.workflow_type !== 'ArcEnCiel' && typeof inputs.lora_name === 'string' && UUID_RE.test(inputs.lora_name)) {
          aiData.workflow_type = 'ArcEnCiel';
        }
      }

      // If a Workflow chunk exists alongside the Prompt chunk, extract per-node
      // provenance (cnr_id / aux_id). ComfyUI ≥1.26 embeds this automatically;
      // it lets us resolve node origins without GitHub code search.
      const provenance = chunks.workflow ? extractWorkflowProvenance(chunks.workflow) : undefined;

      // Scan entire workflow JSON for Civitai URN:AIR resource identifiers.
      // Format: urn:air:{baseModel}:{type}:civitai:{modelId}@{versionId}
      // These appear in lora_name, model_name, and other input fields.
      const URN_AIR_RE = /urn:air:([^:]+):([^:]+):civitai:(\d+)@(\d+)/g;
      const workflowStr = JSON.stringify(workflow);
      const seenUrns = new Set<string>();
      const civitaiUrnResources: Array<{ urn: string; baseModel: string; type: string; modelId: string; versionId: string }> = [];
      for (const m of workflowStr.matchAll(URN_AIR_RE)) {
        if (!seenUrns.has(m[0])) {
          seenUrns.add(m[0]);
          civitaiUrnResources.push({ urn: m[0], baseModel: m[1], type: m[2], modelId: m[3], versionId: m[4] });
        }
      }
      if (civitaiUrnResources.length > 0) {
        aiData.civitai_urn_resources = civitaiUrnResources;
        // URN:AIR presence is authoritative: this workflow was generated by Civitai
        if (aiData.workflow_type === 'ComfyUI') aiData.workflow_type = 'Civitai';
      }

      // Classify all class_types FIRST (extension-map + Workflow provenance),
      // so the traversal in extractComfyUIParams can recognise custom nodes.
      const nodeInfo = await classifyComfyUIWorkflow(workflow, provenance);
      if (nodeInfo) {
        aiData.comfyui_nodes = nodeInfo;
      }

      // Extract useful parameters from workflow, feeding the classifications
      // in so Phase 3 can treat known custom nodes with text-shaped inputs as
      // candidate text encoders.
      const extracted = extractComfyUIParams(workflow, nodeInfo?.classifications ?? {});
      Object.assign(aiData, extracted);
      // Restore workflow_type — extractComfyUIParams doesn't set it but Object.assign
      // could theoretically clobber it if the extracted object ever grows that key.
      if (!aiData.workflow_type) aiData.workflow_type = 'ComfyUI';
    } catch (e) {
      // Not valid JSON, store as-is
      aiData.prompt = chunks.prompt;
    }
  }

  // --- NovelAI: Software chunk = "NovelAI" is the authoritative signal ---
  if (chunks.Software === 'NovelAI' && !aiData.workflow_type) {
    aiData.workflow_type = 'NovelAI';
  }

  // NovelAI / Midjourney: Comment or Description PNG chunk
  if (chunks.Comment || chunks.Description) {
    const commentText = chunks.Comment || chunks.Description;
    try {
      const novelData = JSON.parse(commentText);
      // NovelAI v3+ can wrap prompt fields in `{ content, image, ... }` objects.
      // Coerce everything before assigning so React never sees a raw object.
      const promptStr = coercePromptValue(novelData.prompt);
      const ucStr = coercePromptValue(novelData.uc);
      if (promptStr) aiData.prompt = promptStr;
      if (ucStr) aiData.negative_prompt = ucStr;
      if (novelData.steps !== undefined) aiData.steps = String(novelData.steps);
      if (novelData.scale !== undefined) aiData.cfg_scale = String(novelData.scale);
      if (novelData.seed !== undefined) aiData.seed = String(novelData.seed);
      if (novelData.sampler !== undefined) aiData.sampler = coercePromptValue(novelData.sampler);
      // NovelAI uses 'uc' for negative prompt; Draw Things uses 'c' for positive
      if (novelData.uc !== undefined && !novelData.c) {
        aiData.workflow_type = 'NovelAI';
      }
    } catch (e) {
      // Not JSON — check for Midjourney format
      // MJ stores prompt + --params + "Job ID: uuid" in Description tEXt chunk
      if (typeof commentText === 'string' && commentText.includes('Job ID:')) {
        aiData.workflow_type = 'Midjourney';
        const jobMatch = commentText.match(/Job ID:\s*([a-f0-9-]+)/i);
        if (jobMatch) aiData.job_id = jobMatch[1];

        // Extract prompt (everything before the first -- param)
        const paramStart = commentText.indexOf(' --');
        if (paramStart > 0) {
          aiData.prompt = commentText.substring(0, paramStart).trim();

          // Parse MJ parameters
          const paramSection = commentText.substring(paramStart);
          const arMatch = paramSection.match(/--ar\s+([\d:]+)/);
          const vMatch = paramSection.match(/--v\s+([\d.]+)/);
          const nijiMatch = paramSection.match(/--niji\s+(\d+)/);
          const sMatch = paramSection.match(/--stylize\s+(\d+)|--s\s+(\d+)/);
          const cMatch = paramSection.match(/--chaos\s+(\d+)|--c\s+(\d+)/);
          const seedMatch = paramSection.match(/--seed\s+(\d+)/);
          const noMatch = paramSection.match(/--no\s+([^-]+?)(?:\s+--|Job ID:|$)/);
          const weirdMatch = paramSection.match(/--weird\s+(\d+)/);
          const qualMatch = paramSection.match(/--quality\s+([\d.]+)|--q\s+([\d.]+)/);
          const styleMatch = paramSection.match(/--style\s+(\S+)/);

          if (arMatch) aiData.aspect_ratio = arMatch[1];
          // --niji overrides --v if both present (they're mutually exclusive MJ model families)
          if (vMatch) aiData.version = `v${vMatch[1]}`;
          if (nijiMatch) aiData.version = `niji ${nijiMatch[1]}`;
          if (sMatch) aiData.stylize = sMatch[1] || sMatch[2];
          if (cMatch) aiData.chaos = cMatch[1] || cMatch[2];
          if (seedMatch) aiData.seed = seedMatch[1];
          if (noMatch) aiData.negative_prompt = noMatch[1].trim();
          if (weirdMatch) aiData.weird = weirdMatch[1];
          if (qualMatch) aiData.quality = qualMatch[1] || qualMatch[2];
          if (styleMatch) aiData.style = styleMatch[1];
        } else {
          // No params, whole thing is the prompt (minus Job ID)
          aiData.prompt = commentText.replace(/\s*Job ID:.*$/, '').trim();
        }
      }
    }
  }

  // Also check "Author" PNG chunk (MJ stores the username there)
  if (chunks.Author && aiData.workflow_type === 'Midjourney') {
    aiData.author = chunks.Author;
  }

  return aiData;
}

// Decode a UserComment byte payload using iconv-lite.
// The EXIF UserComment spec: first 8 bytes = encoding ID, rest = encoded text.
// Known prefixes: "ASCII\0\0\0", "UNICODE\0" (UTF-16), "JIS\0\0\0\0\0" (Shift-JIS)
// Some tools write raw bytes with no prefix at all.
function decodeUserComment(raw: Buffer): string | null {
  if (raw.length < 8) return null;

  const prefix = raw.slice(0, 8);
  const payload = raw.slice(8);

  // UNICODE prefix → UTF-16 (Civitai, some A1111 forks)
  if (prefix.indexOf('UNICODE') === 0) {
    // Detect BOM: if first two bytes are FF FE → LE, FE FF → BE
    if (payload.length >= 2 && payload[0] === 0xFF && payload[1] === 0xFE) {
      return iconv.decode(payload.slice(2), 'utf-16le').replace(/\0+$/, '').trim();
    }
    if (payload.length >= 2 && payload[0] === 0xFE && payload[1] === 0xFF) {
      return iconv.decode(payload.slice(2), 'utf-16be').replace(/\0+$/, '').trim();
    }
    // No BOM — detect byte order by checking null byte positions.
    // In UTF-16-LE ASCII text: XX 00 XX 00 (every odd byte is 00)
    // In UTF-16-BE ASCII text: 00 XX 00 XX (every even byte is 00)
    const encoding = detectUTF16ByteOrder(payload);
    const decoded = iconv.decode(payload, encoding).replace(/\0+$/, '').trim();
    // If result still looks like mojibake (CJK where ASCII expected), try the other order
    if (hasMojibake(decoded) || looksLikeByteSwappedASCII(decoded)) {
      const altEncoding = encoding === 'utf-16le' ? 'utf-16be' : 'utf-16le';
      const altDecoded = iconv.decode(payload, altEncoding).replace(/\0+$/, '').trim();
      if (!hasMojibake(altDecoded) && !looksLikeByteSwappedASCII(altDecoded)) {
        return altDecoded;
      }
    }
    return decoded;
  }

  // ASCII prefix → UTF-8
  if (prefix.indexOf('ASCII') === 0) {
    return payload.toString('utf8').replace(/\0+$/, '').trim();
  }

  // JIS prefix → Shift-JIS (Japanese tools)
  if (prefix.indexOf('JIS') === 0) {
    return iconv.decode(payload, 'shiftjis').replace(/\0+$/, '').trim();
  }

  // No recognized prefix — try UTF-8 first, then common fallbacks
  const utf8 = raw.toString('utf8').replace(/\0+$/, '').trim();
  // Check for mojibake indicators (common in mis-encoded text)
  if (!hasMojibake(utf8) && utf8.length > 0) return utf8;

  // Try Shift-JIS
  try {
    const sjis = iconv.decode(raw, 'shiftjis').replace(/\0+$/, '').trim();
    if (sjis.length > 0 && !hasMojibake(sjis)) return sjis;
  } catch { /* skip */ }

  // Try Windows-1252 (Latin)
  try {
    const latin = iconv.decode(raw, 'windows-1252').replace(/\0+$/, '').trim();
    if (latin.length > 0) return latin;
  } catch { /* skip */ }

  // Give back the UTF-8 attempt as last resort
  return utf8.length > 0 ? utf8 : null;
}

// Quick heuristic: does the string look like mojibake?
// Looks for sequences of replacement chars or implausible byte patterns
function hasMojibake(text: string): boolean {
  // Unicode replacement characters
  if (text.includes('\uFFFD')) return true;
  // Runs of C2/C3 + high bytes (classic UTF-8-decoded-as-Latin mojibake)
  if (/[\u00C2\u00C3][\u0080-\u00BF]{2,}/.test(text)) return true;
  return false;
}

// Detect UTF-16 byte order by sampling null byte positions.
// ASCII text in UTF-16-LE: byte pairs are [char, 0x00] — odd positions are 0x00
// ASCII text in UTF-16-BE: byte pairs are [0x00, char] — even positions are 0x00
function detectUTF16ByteOrder(data: Buffer): 'utf-16le' | 'utf-16be' {
  let leScore = 0; // odd bytes are 0x00 → LE
  let beScore = 0; // even bytes are 0x00 → BE
  const sampleSize = Math.min(data.length, 64); // check first 32 code units
  for (let i = 0; i < sampleSize - 1; i += 2) {
    if (data[i] !== 0 && data[i + 1] === 0) leScore++;
    if (data[i] === 0 && data[i + 1] !== 0) beScore++;
  }
  return beScore > leScore ? 'utf-16be' : 'utf-16le';
}

// Detect byte-swapped ASCII: CJK chars in the U+6000-U+7A00 range that map to
// ASCII a-z/A-Z when byte-swapped (e.g. 瀀=U+7000 is really 'p'=U+0070 swapped)
function looksLikeByteSwappedASCII(text: string): boolean {
  if (text.length < 5) return false;
  let suspiciousCount = 0;
  const sampleLen = Math.min(text.length, 50);
  for (let i = 0; i < sampleLen; i++) {
    const code = text.charCodeAt(i);
    // CJK Unified Ideographs range that maps to ASCII when byte-swapped
    // ASCII 0x20-0x7E → swapped becomes 0x2000-0x7E00
    if (code >= 0x2000 && code <= 0x7F00 && (code & 0xFF) === 0) {
      suspiciousCount++;
    }
  }
  // If more than 40% of sampled chars look byte-swapped, it's likely wrong endianness
  return suspiciousCount / sampleLen > 0.4;
}

// Extract AI metadata from JPEG EXIF UserComment field.
// Different tools encode UserComment differently:
//   - Civitai: "UNICODE\0" prefix + UTF-16-LE text (A1111-style params)
//   - ComfyUI: "ASCII\0\0\0" prefix + UTF-8 JSON, or raw UTF-8 JSON
//   - A1111: may use ASCII prefix or raw text
//   - Japanese tools: JIS prefix + Shift-JIS
//
// Proper approach: parse the TIFF IFD structure to find the UserComment tag,
// read its offset and byte count, then decode only the exact data bytes.
function parseJPEGUserComment(buffer: Buffer): string | null {
  try {
    let offset = 2; // Skip JPEG SOI marker (FF D8)

    while (offset < buffer.length - 4) {
      if (buffer[offset] !== 0xFF) { offset++; continue; }
      const marker = buffer[offset + 1];
      if (marker === 0xDA) break; // SOS — no more metadata after this

      // APP1 = 0xE1 (EXIF lives here)
      if (marker === 0xE1) {
        const segLength = (buffer[offset + 2] << 8) | buffer[offset + 3];
        const segEnd = offset + 2 + segLength;
        const segData = buffer.slice(offset + 4, segEnd);

        // Try proper TIFF-based extraction first
        const fromTIFF = extractUserCommentFromTIFF(segData);
        if (fromTIFF) return fromTIFF;

        // Fallback: scan entire segment for encoding prefixes
        const fromScan = scanForUserComment(segData);
        if (fromScan) return fromScan;

        offset = segEnd;
        continue;
      }

      // Skip other marker segments
      if ((marker >= 0xE0 && marker <= 0xEF) || marker === 0xFE) {
        const segLength = (buffer[offset + 2] << 8) | buffer[offset + 3];
        offset += 2 + segLength;
      } else {
        offset++;
      }
    }
  } catch (e) {
    console.error('parseJPEGUserComment error:', e);
  }
  return null;
}

// Parse the TIFF structure inside an APP1 segment to find UserComment (tag 0x9286).
// This correctly handles byte order (II = little-endian, MM = big-endian).
function extractUserCommentFromTIFF(segData: Buffer): string | null {
  // APP1 starts with "Exif\0\0" (6 bytes), then TIFF header
  if (segData.length < 14) return null;
  const exifHeader = segData.toString('ascii', 0, 4);
  if (exifHeader !== 'Exif') return null;

  const tiffStart = 6; // offset within segData where TIFF header begins
  const tiffData = segData.slice(tiffStart);
  const byteOrder = tiffData.toString('ascii', 0, 2);
  const isLE = byteOrder === 'II';
  const isBE = byteOrder === 'MM';
  if (!isLE && !isBE) return null;

  // All offsets in TIFF are relative to tiffStart (the TIFF header)
  const read16 = (off: number) => {
    if (off + 2 > tiffData.length) return 0;
    return isLE ? tiffData.readUInt16LE(off) : tiffData.readUInt16BE(off);
  };
  const read32 = (off: number) => {
    if (off + 4 > tiffData.length) return 0;
    return isLE ? tiffData.readUInt32LE(off) : tiffData.readUInt32BE(off);
  };

  // Verify TIFF magic (42)
  if (read16(2) !== 42) return null;

  const ifd0Offset = read32(4);

  // Read a 4-byte value from an IFD entry's value field (used for pointers like EXIF IFD offset)
  function findIFDEntryValue(ifdOffset: number, targetTag: number): number | null {
    if (ifdOffset + 2 > tiffData.length) return null;
    const entryCount = read16(ifdOffset);
    for (let i = 0; i < entryCount; i++) {
      const entryOff = ifdOffset + 2 + i * 12;
      if (entryOff + 12 > tiffData.length) break;
      if (read16(entryOff) === targetTag) {
        return read32(entryOff + 8); // value/offset field
      }
    }
    return null;
  }

  // Find UserComment data (tag 0x9286) in an IFD — returns raw bytes
  function findUserComment(ifdOffset: number): Buffer | null {
    if (ifdOffset + 2 > tiffData.length) return null;
    const entryCount = read16(ifdOffset);
    for (let i = 0; i < entryCount; i++) {
      const entryOff = ifdOffset + 2 + i * 12;
      if (entryOff + 12 > tiffData.length) break;
      if (read16(entryOff) !== 0x9286) continue;

      // Type 7 = UNDEFINED, 1 byte per element
      const byteCount = read32(entryOff + 4);
      if (byteCount < 8) return null;

      let dataStart: number;
      if (byteCount <= 4) {
        dataStart = entryOff + 8; // inline
      } else {
        dataStart = read32(entryOff + 8); // offset from TIFF header
      }

      if (dataStart + byteCount > tiffData.length) return null;
      return tiffData.slice(dataStart, dataStart + byteCount);
    }
    return null;
  }

  // Find EXIF sub-IFD pointer (tag 0x8769) in IFD0
  const exifIFDOffset = findIFDEntryValue(ifd0Offset, 0x8769);
  if (exifIFDOffset === null) return null;

  // Find UserComment in EXIF IFD
  const ucRaw = findUserComment(exifIFDOffset);
  if (!ucRaw) return null;

  const decoded = decodeUserComment(ucRaw);
  if (decoded && decoded.length > 5) return decoded;

  return null;
}

// Fallback: scan segment bytes for encoding prefixes (handles non-standard EXIF)
function scanForUserComment(segData: Buffer): string | null {
  for (const prefix of ['UNICODE', 'ASCII\0\0\0', 'JIS\0\0\0\0\0']) {
    const idx = segData.indexOf(prefix);
    if (idx === -1) continue;

    // Try to determine data length: scan for a run of null bytes after text
    // or use a reasonable max length
    let endIdx = idx + 8; // skip prefix
    const maxEnd = Math.min(segData.length, idx + 65536);

    if (prefix === 'UNICODE') {
      // UTF-16-LE: scan for 4+ consecutive null bytes (end of text region)
      endIdx = idx + 8;
      while (endIdx + 3 < maxEnd) {
        if (segData[endIdx] === 0 && segData[endIdx + 1] === 0 &&
            segData[endIdx + 2] === 0 && segData[endIdx + 3] === 0) {
          break;
        }
        endIdx += 2; // advance by UTF-16 code unit
      }
      endIdx = Math.min(endIdx + 2, maxEnd); // include last char
    } else {
      // ASCII/JIS: scan for null terminator
      while (endIdx < maxEnd && segData[endIdx] !== 0) endIdx++;
    }

    const commentRaw = segData.slice(idx, endIdx);
    const decoded = decodeUserComment(commentRaw);
    if (decoded && decoded.length > 5 && (decoded.includes('Steps:') || decoded.startsWith('{') || decoded.length > 20)) {
      return decoded;
    }
  }

  // Also try finding raw JSON or A1111 params without prefix
  const jsonStart = segData.indexOf('{'.charCodeAt(0));
  if (jsonStart !== -1) {
    // Try to find matching closing brace
    let braceDepth = 0;
    let jsonEnd = jsonStart;
    for (let i = jsonStart; i < Math.min(segData.length, jsonStart + 65536); i++) {
      if (segData[i] === 0x7B) braceDepth++;
      else if (segData[i] === 0x7D) { braceDepth--; if (braceDepth === 0) { jsonEnd = i + 1; break; } }
    }
    if (jsonEnd > jsonStart) {
      const possibleJson = segData.slice(jsonStart, jsonEnd).toString('utf8').trim();
      try { JSON.parse(possibleJson); return possibleJson; } catch { /* not valid json */ }
    }
  }

  const stepsIdx = segData.indexOf('Steps:');
  if (stepsIdx !== -1) {
    let textStart = stepsIdx;
    while (textStart > 0 && segData[textStart - 1] !== 0) textStart--;
    const comment = segData.slice(textStart, Math.min(segData.length, stepsIdx + 4096)).toString('utf8').replace(/\0+$/, '').trim();
    if (comment.length > 10) return comment;
  }

  return null;
}

// ============================================================================
// XMP Extraction — XML-based metadata (Midjourney, Draw Things, Mochi, cameras)
// ============================================================================

// Extract raw XMP XML string from a file buffer (works for PNG, JPEG, WebP, TIFF)
function extractXMPString(buffer: Buffer): string | null {
  // Method 1: Search for XMP packet markers directly in the buffer.
  // This works across all formats since XMP is always valid XML text.
  const startMarker = '<x:xmpmeta';
  const endMarker = '</x:xmpmeta>';

  const startIdx = buffer.indexOf(startMarker);
  if (startIdx === -1) return null;

  const endIdx = buffer.indexOf(endMarker, startIdx);
  if (endIdx === -1) return null;

  return buffer.slice(startIdx, endIdx + endMarker.length).toString('utf8');
}

// Parse XMP XML into a flat key-value object using regex.
// No XML parser needed — XMP is structured enough for pattern matching.
function parseXMP(xmpString: string): Record<string, any> {
  const xmp: Record<string, any> = {};

  // Extract all simple property values: <ns:Key>Value</ns:Key>
  const simpleProps = xmpString.matchAll(/<([a-zA-Z_][\w]*):([a-zA-Z_][\w]*)(?:\s[^>]*)?>([^<]+)<\/\1:\2>/g);
  for (const match of simpleProps) {
    const ns = match[1];
    const key = match[2];
    const value = match[3].trim();
    if (value) {
      // Use namespace:key for clarity, but also store common ones with friendly names
      xmp[`${ns}:${key}`] = value;
    }
  }

  // Extract attribute-based values: ns:Key="value"
  const attrProps = xmpString.matchAll(/\s([a-zA-Z_][\w]*):([a-zA-Z_][\w]*)="([^"]+)"/g);
  for (const match of attrProps) {
    const ns = match[1];
    const key = match[2];
    const value = match[3].trim();
    if (value && ns !== 'xmlns' && ns !== 'x' && ns !== 'rdf') {
      xmp[`${ns}:${key}`] = value;
    }
  }

  // Extract rdf:li items (used for lists like dc:subject tags, dc:description, exif:UserComment)
  // These can contain large text blobs, JSON, or multi-line content
  const listBlocks = xmpString.matchAll(/<([a-zA-Z_][\w]*):([a-zA-Z_][\w]*)\s*>\s*<rdf:(?:Bag|Seq|Alt)\s*>([\s\S]*?)<\/rdf:(?:Bag|Seq|Alt)>/g);
  for (const block of listBlocks) {
    const ns = block[1];
    const key = block[2];
    const itemsRaw = block[3];
    // Use [\s\S]*? to match ANY content inside rdf:li, including newlines, JSON, XML entities
    const items = [...itemsRaw.matchAll(/<rdf:li[^>]*>([\s\S]*?)<\/rdf:li>/g)]
      .map(m => m[1].trim().replace(/&#xA;/g, '\n').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"'))
      .filter(Boolean);
    if (items.length > 0) {
      xmp[`${ns}:${key}`] = items.length === 1 ? items[0] : items;
    }
  }

  return xmp;
}

// Extract AI-specific metadata from XMP data
function extractAIFromXMP(xmp: Record<string, any>): Record<string, any> {
  const ai: Record<string, any> = {};

  // --- Midjourney ---
  // MJ stores prompt in dc:description and sometimes in xmp:Description
  // Job ID, version info may be in other fields
  const description = xmp['dc:description'];
  if (typeof description === 'string' && description.length > 20) {
    // Midjourney descriptions often contain the full prompt with --parameters
    const mjParamMatch = description.match(/^([\s\S]+?)\s+--/);
    if (mjParamMatch) {
      ai.prompt = mjParamMatch[1].trim();
      ai.workflow_type = 'Midjourney';
      // Extract MJ parameters
      const arMatch = description.match(/--ar\s+([\d:]+)/);
      const vMatch = description.match(/--v\s+([\d.]+)/);
      const sMatch = description.match(/--s\s+(\d+)/);
      const cMatch = description.match(/--c\s+(\d+)/);
      const seedMatch = description.match(/--seed\s+(\d+)/);
      const noMatch = description.match(/--no\s+([^-]+)/);
      if (arMatch) ai.aspect_ratio = arMatch[1];
      if (vMatch) ai.version = `v${vMatch[1]}`;
      if (sMatch) ai.stylize = sMatch[1];
      if (cMatch) ai.chaos = cMatch[1];
      if (seedMatch) ai.seed = seedMatch[1];
      if (noMatch) ai.negative_prompt = noMatch[1].trim();
    } else if (!ai.prompt) {
      ai.prompt = description;
    }
  }

  // --- Draw Things ---
  // Draw Things stores rich JSON in exif:UserComment AND A1111-style text in dc:description
  const software = xmp['xmp:CreatorTool'] || xmp['tiff:Software'] || '';
  const isDrawThings = typeof software === 'string' && software.toLowerCase().includes('draw things');

  const userComment = xmp['exif:UserComment'] || xmp['tiff:ImageDescription'];
  if (typeof userComment === 'string' && userComment.length > 10) {
    try {
      const parsed = JSON.parse(userComment);
      // Draw Things JSON format
      if (parsed.c || parsed.model || parsed.sampler) {
        ai.workflow_type = 'Draw Things';
        const promptStr = coercePromptValue(parsed.c);
        const negStr = coercePromptValue(parsed.uc);
        if (promptStr) ai.prompt = promptStr;
        if (negStr) ai.negative_prompt = negStr;
        if (parsed.model) ai.model = coercePromptValue(parsed.model);
        if (parsed.sampler) ai.sampler = coercePromptValue(parsed.sampler);
        if (parsed.steps) ai.steps = String(parsed.steps);
        if (parsed.scale) ai.cfg_scale = String(parsed.scale);
        if (parsed.seed) ai.seed = String(parsed.seed);
        if (parsed.size) ai.size = coercePromptValue(parsed.size);
        if (parsed.seed_mode) ai.seed_mode = coercePromptValue(parsed.seed_mode);
        if (parsed.strength) ai.strength = String(parsed.strength);
        // LoRAs
        if (Array.isArray(parsed.lora) && parsed.lora.length > 0) {
          ai.loras = parsed.lora.map((l: any) => `${l.model} (${l.weight})`);
        }
      } else if (parsed.prompt) {
        // Coerce per-field rather than spreading raw JSON, which can drop
        // object-shaped fields straight into the AI tab as React children.
        const promptStr = coercePromptValue(parsed.prompt);
        if (promptStr) ai.prompt = promptStr;
        const negStr = coercePromptValue(parsed.negative_prompt ?? parsed.uc);
        if (negStr) ai.negative_prompt = negStr;
        for (const [k, v] of Object.entries(parsed)) {
          if (k === 'prompt' || k === 'negative_prompt' || k === 'uc') continue;
          if (ai[k] !== undefined) continue;
          const coerced = coercePromptValue(v);
          if (coerced !== undefined) ai[k] = coerced;
        }
      }
    } catch {
      // Not JSON — try A1111-style text
      if (userComment.includes('Steps:')) {
        ai._drawthings_params = userComment;
      }
    }
  }

  // If dc:description has A1111-style params (Draw Things also puts them there)
  if (isDrawThings && typeof description === 'string' && description.includes('Steps:') && !ai.prompt) {
    ai._drawthings_params = description;
  }

  // --- Common AI XMP fields ---
  const creator = xmp['dc:creator'];
  if (creator) ai.creator_tool = typeof creator === 'string' ? creator : Array.isArray(creator) ? creator.join(', ') : undefined;

  if (software && !ai.software) ai.software = software;

  // Photoshop/Adobe fields that may indicate AI generation
  const history = xmp['xmpMM:History'];
  if (typeof history === 'string' && (history.includes('firefly') || history.includes('generative'))) {
    ai.workflow_type = ai.workflow_type || 'Adobe Firefly';
  }

  return ai;
}

// Detect the actual image format from magic bytes, ignoring file extension.
// CDNs (Civitai, etc.) sometimes serve PNG files with a .jpeg extension.
// Returns null if the format is not recognised.
// Extract image dimensions without relying on EXIF data.
// PNG: read IHDR (always the first chunk, width/height at fixed offsets).
// JPEG: scan for the first SOF marker.
function extractImageDimensions(buffer: Buffer, mimeType: string): { width: number; height: number } | null {
  if (mimeType === 'image/png' && buffer.length >= 24) {
    // After the 8-byte PNG signature: 4-byte chunk length + 4-byte "IHDR" type,
    // then the IHDR data: width (4 bytes BE) at offset 16, height at offset 20.
    const width = buffer.readUInt32BE(16);
    const height = buffer.readUInt32BE(20);
    if (width > 0 && height > 0) return { width, height };
  } else if (mimeType === 'image/jpeg') {
    let offset = 2; // Skip SOI marker (FF D8)
    while (offset + 3 < buffer.length) {
      if (buffer[offset] !== 0xFF) break;
      const marker = buffer[offset + 1];
      const segLen = buffer.readUInt16BE(offset + 2);
      // SOF0-SOF3, SOF5-SOF7, SOF9-SOF11, SOF13-SOF15 carry dimensions.
      // Exclude 0xC4 (DHT), 0xC8 (reserved), 0xCC (DAC).
      if (marker !== 0xC4 && marker !== 0xC8 && marker !== 0xCC &&
          ((marker >= 0xC0 && marker <= 0xC3) || (marker >= 0xC5 && marker <= 0xC7) ||
           (marker >= 0xC9 && marker <= 0xCB) || (marker >= 0xCD && marker <= 0xCF))) {
        if (offset + 8 < buffer.length) {
          const height = buffer.readUInt16BE(offset + 5);
          const width = buffer.readUInt16BE(offset + 7);
          if (width > 0 && height > 0) return { width, height };
        }
      }
      offset += 2 + segLen;
    }
  }
  return null;
}

function detectMimeFromMagic(buffer: Buffer): string | null {
  if (buffer.length < 4) return null;
  // PNG: 89 50 4E 47 0D 0A 1A 0A
  if (buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47) {
    return 'image/png';
  }
  // JPEG: FF D8 FF
  if (buffer[0] === 0xFF && buffer[1] === 0xD8 && buffer[2] === 0xFF) {
    return 'image/jpeg';
  }
  // WebP: RIFF????WEBP
  if (
    buffer.length >= 12 &&
    buffer.toString('ascii', 0, 4) === 'RIFF' &&
    buffer.toString('ascii', 8, 12) === 'WEBP'
  ) {
    return 'image/webp';
  }
  return null;
}

// Shared extraction function used by both GET (path-based) and POST (file upload)
export async function extractMetadataFromBuffer(
  buffer: Buffer,
  mimeType: string,
  fileName: string,
  fileSize: number,
  lastModified: string,
): Promise<Record<string, any>> {
  // Trust file content over extension — CDNs can mislabel format in the filename.
  const effectiveMime = detectMimeFromMagic(buffer) ?? mimeType;

  let exifData = {};
  let iptcData = {};

  // Try to parse EXIF data (only works for JPEG/TIFF)
  try {
    const parser = exifParser.create(buffer);
    const result = parser.parse();
    exifData = result.tags || {};
    iptcData = result.iptc || {};
  } catch (e) {
    // EXIF parsing failed, that's ok for PNGs
  }

  // Parse PNG chunks for AI metadata
  let aiData: Record<string, any> = {};
  if (effectiveMime === 'image/png') {
    const chunks = parsePNGChunks(buffer);
    aiData = await parseAIMetadata(chunks);
  } else if (effectiveMime === 'image/jpeg') {
    let userComment = parseJPEGUserComment(buffer);

    if (!userComment && (exifData as any).UserComment) {
      const epComment = String((exifData as any).UserComment).trim();
      if (epComment.length > 10 && (epComment.includes('Steps:') || epComment.startsWith('{'))) {
        userComment = epComment;
      }
    }

    if (userComment) {
      if (userComment.trim().startsWith('{')) {
        aiData = await parseAIMetadata({ prompt: userComment });
      } else {
        aiData = await parseAIMetadata({ parameters: userComment });
      }
    }
  }

  // Extract XMP metadata (works for all image formats)
  let xmpData: Record<string, any> = {};
  const xmpString = extractXMPString(buffer);
  if (xmpString) {
    xmpData = parseXMP(xmpString);

    const xmpAI = extractAIFromXMP(xmpData);
    if (Object.keys(xmpAI).length > 0) {
      if (xmpAI._drawthings_params) {
        const dtParams = xmpAI._drawthings_params;
        delete xmpAI._drawthings_params;
        const dtParsed = await parseAIMetadata({ parameters: dtParams });
        Object.assign(aiData, dtParsed);
      }
      for (const [key, value] of Object.entries(xmpAI)) {
        if (!aiData[key]) aiData[key] = value;
      }
    }
  }

  const dims = extractImageDimensions(buffer, effectiveMime);

  return {
    fileName,
    fileSize,
    fileType: effectiveMime,
    lastModified,
    ...(dims ?? {}),
    exif: exifData,
    iptc: iptcData,
    xmp: xmpData,
    ai: aiData,
  };
}

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const filePath = searchParams.get('path');
  const baseFolder = searchParams.get('baseFolder') || '.';

  if (!filePath) {
    return NextResponse.json({ error: 'File path is required' }, { status: 400 });
  }

  const resolvedBase = path.resolve(baseFolder);
  const fullPath = path.isAbsolute(filePath) ? filePath : path.join(resolvedBase, filePath);
  const resolvedPath = path.resolve(fullPath);

  if (!resolvedPath.startsWith(resolvedBase)) {
    return NextResponse.json({ error: 'Access denied - path outside base folder' }, { status: 403 });
  }

  try {
    const file = await fs.readFile(resolvedPath);
    const stats = await fs.stat(resolvedPath);
    const mimeType = mime.lookup(resolvedPath) || 'application/octet-stream';

    const metadata = await extractMetadataFromBuffer(
      file,
      mimeType,
      path.basename(resolvedPath),
      stats.size,
      stats.mtime.toISOString(),
    );

    return NextResponse.json(metadata);
  } catch (error) {
    console.error('Metadata extraction error:', error);
    if (error instanceof Error) {
      if ('code' in error && error.code === 'ENOENT') {
        return NextResponse.json({ error: 'File not found' }, { status: 404 });
      }
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    return NextResponse.json({ error: 'An unknown error occurred' }, { status: 500 });
  }
}
