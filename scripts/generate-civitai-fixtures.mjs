/**
 * Generates synthetic test PNGs with Civitai-style metadata chunks, no deps.
 *
 * Fixture 1 (civitai-onsite.png): A1111-style `parameters` tEXt chunk whose
 *   params contain "Civitai resources: [...]" — exercises the on-site
 *   generator path (workflow_type 'Civitai', civitai_resources).
 * Fixture 2 (civitai-comfyui-urn.png): ComfyUI `prompt`/`workflow` tEXt
 *   chunks whose node properties contain urn:air:...:civitai:ID@VER —
 *   exercises the URN:AIR provenance path.
 *
 * Usage: node scripts/generate-civitai-fixtures.mjs
 */
import fs from 'fs';
import path from 'path';
import zlib from 'zlib';

const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(buf) {
  let c = 0xffffffff;
  for (const b of buf) c = CRC_TABLE[(c ^ b) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const typeBuf = Buffer.from(type, 'ascii');
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])));
  return Buffer.concat([len, typeBuf, data, crc]);
}

function tEXt(keyword, text) {
  return chunk('tEXt', Buffer.concat([Buffer.from(keyword, 'latin1'), Buffer.from([0]), Buffer.from(text, 'latin1')]));
}

function minimalPNG(extraChunks) {
  // 1x1 red RGB image
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(1, 0); ihdr.writeUInt32BE(1, 4);
  ihdr[8] = 8; ihdr[9] = 2; // 8-bit, truecolor
  const raw = Buffer.from([0, 255, 0, 0]); // filter byte + RGB
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    ...extraChunks,
    chunk('IDAT', zlib.deflateSync(raw)),
    chunk('IEND', Buffer.alloc(0)),
  ]);
}

const onsiteParams =
  'masterpiece, a red pixel\n' +
  'Negative prompt: blurry\n' +
  'Steps: 20, Sampler: Euler a, CFG scale: 7, Seed: 12345, Size: 512x512, ' +
  'Civitai resources: [{"type":"checkpoint","modelVersionId":152608,"modelId":133733,"name":"SomeModel"}]';

// Minimal ComfyUI graph: a KSampler-ish node with a URN:AIR checkpoint link
const comfyPrompt = JSON.stringify({
  '1': {
    class_type: 'CheckpointLoaderSimple',
    inputs: { ckpt_name: 'urn:air:sdxl:checkpoint:civitai:133733@152608' },
    _meta: { title: 'Load Checkpoint' },
  },
  '2': {
    class_type: 'KSampler',
    inputs: { seed: 12345, steps: 20, cfg: 7, sampler_name: 'euler_ancestral', model: ['1', 0] },
    _meta: { title: 'KSampler' },
  },
});
const comfyWorkflow = JSON.stringify({
  last_node_id: 2, last_link_id: 1, version: 1,
  nodes: [{ id: 1, type: 'CheckpointLoaderSimple', properties: { 'Node name for S&R': 'CheckpointLoaderSimple' } }],
});

const outDir = path.resolve('fixtures');
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, 'civitai-onsite.png'), minimalPNG([tEXt('parameters', onsiteParams)]));
fs.writeFileSync(path.join(outDir, 'civitai-comfyui-urn.png'), minimalPNG([tEXt('prompt', comfyPrompt), tEXt('workflow', comfyWorkflow)]));
console.log('fixtures written to', outDir);
