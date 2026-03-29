import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';
import mime from 'mime-types';
import exifParser from 'exif-parser';
import iconv from 'iconv-lite';

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

// Walk backwards from a node input, collecting ancestor nodes up to maxDepth.
// `hint` tells the tracer what kind of data we're looking for (e.g. "positive", "negative")
// so combo nodes like Efficient Loader route us down the right input branch.
function traceBack(
  workflow: Record<string, any>,
  startRef: any,
  hint?: string,
  maxDepth: number = 10,
  visited?: Set<string>,
  skipNodes?: Set<string>
): Array<{ nodeId: string; node: any; depth: number }> {
  const results: Array<{ nodeId: string; node: any; depth: number }> = [];
  const seen = visited || new Set<string>();

  function walk(ref: any, depth: number, currentHint?: string) {
    if (depth > maxDepth) return;
    const target = followRef(workflow, ref, new Set());
    if (!target || seen.has(target.nodeId)) return;
    if (skipNodes?.has(target.nodeId)) return; // skip muted/bypassed nodes
    seen.add(target.nodeId);
    results.push({ ...target, depth });

    const inputs = target.node.inputs || {};

    // If we have a hint and this node has a matching input name, prefer that path.
    // This handles combo nodes (e.g. Efficient Loader with both positive/negative inputs)
    if (currentHint && isNodeRef(inputs[currentHint])) {
      walk(inputs[currentHint], depth + 1, currentHint);
      return; // Only follow the hinted path on combo nodes
    }

    // If the hint matches a direct string value on this node, we found what we need —
    // no need to walk further from here
    if (currentHint && typeof inputs[currentHint] === 'string') {
      return;
    }

    // Otherwise walk all ref inputs
    for (const [key, val] of Object.entries(inputs)) {
      if (isNodeRef(val)) walk(val, depth + 1, currentHint);
    }
  }

  walk(startRef, 0, hint);
  return results;
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
    const hintLower = hint.toLowerCase();
    for (const [key, val] of Object.entries(inputs)) {
      const keyUpper = key.toUpperCase();
      if ((keyUpper.includes(hintUpper) || keyUpper.includes(hintLower.toUpperCase())) &&
          (keyUpper.includes('PROMPT') || keyUpper.includes('TEXT') || keyUpper.includes('STRING'))) {
        if (typeof val === 'string' && val.trim()) return val;
      }
    }
    // Also check just the hint name directly (e.g. inputs.positive, inputs.negative)
    if (typeof inputs[hint] === 'string' && inputs[hint].trim()) return inputs[hint];
  }

  // Priority 2: known common text field names
  const textKeys = ['text', 'string', 'text_a', 'text_b', 'value', 'user_prompt', 'prompt', 'text_g', 'text_l'];
  for (const key of textKeys) {
    if (typeof inputs[key] === 'string' && inputs[key].trim()) return inputs[key];
    if (isNodeRef(inputs[key])) {
      const upstream = followRef(workflow, inputs[key], visited);
      if (upstream) {
        const text = findText(workflow, upstream.node, visited, hint);
        if (text) return text;
      }
    }
  }

  // Priority 3: scan all string inputs that look like prompts (longer than ~10 chars,
  // not a filename or simple config value)
  let bestText: string | null = null;
  for (const [key, val] of Object.entries(inputs)) {
    if (typeof val === 'string' && val.trim().length > 10) {
      // Skip fields that are clearly not prompts
      const keyLower = key.toLowerCase();
      if (keyLower.includes('name') || keyLower.includes('file') || keyLower.includes('path') ||
          keyLower.includes('method') || keyLower.includes('mode')) continue;
      if (!bestText || val.length > bestText.length) bestText = val;
    }
  }
  if (bestText) return bestText;

  return null;
}

// ---- Field-based node identification (no type names needed) ----
function hasFields(inputs: any, ...fields: string[]): boolean {
  return fields.every(f => inputs[f] !== undefined);
}

function isSamplerByFields(inputs: any): boolean {
  // A sampler has some combo of: steps, cfg, sampler_name, seed, positive, negative
  const samplerFields = ['steps', 'cfg', 'sampler_name', 'seed', 'positive', 'negative'];
  const matched = samplerFields.filter(f => inputs[f] !== undefined);
  return matched.length >= 3; // at least 3 of these = almost certainly a sampler
}

function isCheckpointByFields(inputs: any): boolean {
  return !!inputs.ckpt_name;
}

function isLatentByFields(inputs: any): boolean {
  return hasFields(inputs, 'width', 'height', 'batch_size');
}

function extractComfyUIParams(workflow: Record<string, any>): Record<string, any> {
  const extracted: Record<string, any> = {};

  // Type-match fallback helper (for platforms that wrap standard nodes)
  const typeMatches = (classType: string, ...patterns: string[]) =>
    patterns.some(p => classType.includes(p));

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
    // Handle numbered LoRA stacker fields (lora_name_1, lora_wt_1, etc.)
    for (const [key, val] of Object.entries(inputs)) {
      const numMatch = key.match(/^lora_name_(\d+)$/);
      if (numMatch && typeof val === 'string' && val !== 'None') {
        // Try to find the matching weight
        const weight = inputs[`lora_wt_${numMatch[1]}`];
        if (typeof weight === 'number') {
          loraSet.add(`${val} (${weight})`);
        } else {
          loraSet.add(val);
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
    if (inputs.sampler_name) extracted.sampler = inputs.sampler_name;
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

    // --- Trace positive conditioning wire ---
    if (isNodeRef(inputs.positive)) {
      const posChain = traceBack(workflow, inputs.positive, 'positive', 10, undefined, mutedNodeIds);
      for (const { node } of posChain) {
        const text = findText(workflow, node, undefined, 'positive');
        if (text) {
          if (!extracted.prompt || text.length > extracted.prompt.length) {
            extracted.prompt = text;
          }
        }
      }
    }

    // --- Trace negative conditioning wire ---
    if (isNodeRef(inputs.negative)) {
      const negChain = traceBack(workflow, inputs.negative, 'negative', 10, undefined, mutedNodeIds);
      for (const { node } of negChain) {
        const text = findText(workflow, node, undefined, 'negative');
        if (text) {
          if (!extracted.negative_prompt || text.length > extracted.negative_prompt.length) {
            extracted.negative_prompt = text;
          }
        }
      }
    }
  }

  // ========================================================================
  // PHASE 3: Type-match fallback
  // If graph tracing didn't find prompts, fall back to type-name scanning
  // ========================================================================
  if (!extracted.prompt) {
    const promptTexts: { text: string; nodeId: string }[] = [];

    for (const [nodeId, nodeData] of Object.entries(workflow)) {
      const node = nodeData as any;
      const classType = node.class_type || '';
      const inputs = node.inputs || {};

      if (typeMatches(classType, 'CLIPTextEncode', 'T5TextEncode', 'FluxTextEncode')) {
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

// Parse AI generation parameters from various formats
function parseAIMetadata(chunks: Record<string, any>): Record<string, any> {
  const aiData: Record<string, any> = {};

  // A1111/Forge format - stored in "parameters" key
  if (chunks.parameters) {
    const params = chunks.parameters;

    // Extract positive prompt (everything before "Negative prompt:")
    const negativeMatch = params.match(/Negative prompt:\s*(.+?)(?:\n|$)/s);
    const splitIndex = params.indexOf('\nNegative prompt:');

    if (splitIndex !== -1) {
      aiData.prompt = params.substring(0, splitIndex).trim();
      if (negativeMatch) {
        aiData.negative_prompt = negativeMatch[1].split('\n')[0].trim();
      }
    } else {
      // No negative prompt found, everything is the positive prompt
      const lines = params.split('\n');
      aiData.prompt = lines[0].trim();
    }

    // Extract generation settings (last line typically)
    const lines = params.split('\n');
    const settingsLine = lines[lines.length - 1];

    // Parse common parameters
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
  }

  // ComfyUI format - stored in "prompt" key (JSON workflow)
  if (chunks.prompt) {
    try {
      // Sanitize NaN/Infinity values that break JSON.parse
      const sanitized = chunks.prompt
        .replace(/:\s*NaN/g, ': null')
        .replace(/:\s*Infinity/g, ': null')
        .replace(/:\s*-Infinity/g, ': null');

      const workflow = JSON.parse(sanitized);
      aiData.comfyui_workflow = workflow;
      aiData.workflow_type = 'ComfyUI';

      // Extract useful parameters from workflow (one-level resolution)
      const extracted = extractComfyUIParams(workflow);
      Object.assign(aiData, extracted);
    } catch (e) {
      // Not valid JSON, store as-is
      aiData.prompt = chunks.prompt;
    }
  }

  // NovelAI format - stored in "Comment" or "Description" key as JSON
  if (chunks.Comment || chunks.Description) {
    const commentText = chunks.Comment || chunks.Description;
    try {
      const novelData = JSON.parse(commentText);
      if (novelData.prompt) aiData.prompt = novelData.prompt;
      if (novelData.uc) aiData.negative_prompt = novelData.uc;
      if (novelData.steps) aiData.steps = novelData.steps;
      if (novelData.scale) aiData.cfg_scale = novelData.scale;
      if (novelData.seed) aiData.seed = novelData.seed;
      if (novelData.sampler) aiData.sampler = novelData.sampler;
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
          const sMatch = paramSection.match(/--stylize\s+(\d+)|--s\s+(\d+)/);
          const cMatch = paramSection.match(/--chaos\s+(\d+)|--c\s+(\d+)/);
          const seedMatch = paramSection.match(/--seed\s+(\d+)/);
          const noMatch = paramSection.match(/--no\s+([^-]+?)(?:\s+--|Job ID:|$)/);
          const weirdMatch = paramSection.match(/--weird\s+(\d+)/);
          const qualMatch = paramSection.match(/--quality\s+([\d.]+)|--q\s+([\d.]+)/);
          const styleMatch = paramSection.match(/--style\s+(\S+)/);

          if (arMatch) aiData.aspect_ratio = arMatch[1];
          if (vMatch) aiData.version = `v${vMatch[1]}`;
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
        if (parsed.c) ai.prompt = parsed.c;
        if (parsed.uc) ai.negative_prompt = parsed.uc;
        if (parsed.model) ai.model = parsed.model;
        if (parsed.sampler) ai.sampler = parsed.sampler;
        if (parsed.steps) ai.steps = String(parsed.steps);
        if (parsed.scale) ai.cfg_scale = String(parsed.scale);
        if (parsed.seed) ai.seed = String(parsed.seed);
        if (parsed.size) ai.size = parsed.size;
        if (parsed.seed_mode) ai.seed_mode = parsed.seed_mode;
        if (parsed.strength) ai.strength = String(parsed.strength);
        // LoRAs
        if (Array.isArray(parsed.lora) && parsed.lora.length > 0) {
          ai.loras = parsed.lora.map((l: any) => `${l.model} (${l.weight})`);
        }
      } else if (parsed.prompt) {
        Object.assign(ai, parsed);
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

// Shared extraction function used by both GET (path-based) and POST (file upload)
export function extractMetadataFromBuffer(
  buffer: Buffer,
  mimeType: string,
  fileName: string,
  fileSize: number,
  lastModified: string,
): Record<string, any> {
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
  if (mimeType === 'image/png') {
    const chunks = parsePNGChunks(buffer);
    aiData = parseAIMetadata(chunks);
  } else if (mimeType === 'image/jpeg') {
    let userComment = parseJPEGUserComment(buffer);

    if (!userComment && (exifData as any).UserComment) {
      const epComment = String((exifData as any).UserComment).trim();
      if (epComment.length > 10 && (epComment.includes('Steps:') || epComment.startsWith('{'))) {
        userComment = epComment;
      }
    }

    if (userComment) {
      if (userComment.trim().startsWith('{')) {
        aiData = parseAIMetadata({ prompt: userComment });
      } else {
        aiData = parseAIMetadata({ parameters: userComment });
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
        const dtParsed = parseAIMetadata({ parameters: dtParams });
        Object.assign(aiData, dtParsed);
      }
      for (const [key, value] of Object.entries(xmpAI)) {
        if (!aiData[key]) aiData[key] = value;
      }
    }
  }

  return {
    fileName,
    fileSize,
    fileType: mimeType,
    lastModified,
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

    const metadata = extractMetadataFromBuffer(
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
