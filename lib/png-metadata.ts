// Dependency-free PNG `tEXt` chunk read/write for the raw-metadata editor.
//
// `app/api/metadata/route.ts` already hand-rolls PNG chunk *parsing*; this is
// the symmetric *encoder*. We deliberately avoid pngjs (and any full PNG codec):
// the image data is never decoded, so every pixel stays byte-for-byte identical
// — only the `tEXt` 'parameters' chunk is swapped. That matters because these
// are finished images the user must not recompress.

const PNG_SIGNATURE = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
// The metadata route parses both spellings; the editor must handle both too so
// existing capital-P chunks are replaced rather than duplicated.
const PARAMETERS_KEYWORDS = new Set(['parameters', 'Parameters']);

interface PngChunk {
  type: string; // 4-char chunk name, e.g. 'tEXt', 'IDAT', 'IEND'
  data: Buffer; // chunk payload (without length / type / crc)
}

// CRC-32 (ITU-T V.42, as used by PNG). Table generated once at module load.
const CRC_TABLE: Uint32Array = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    }
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(buf: Buffer): number {
  let crc = 0xffffffff;
  for (let i = 0; i < buf.length; i++) {
    crc = CRC_TABLE[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8);
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function isPng(buf: Buffer): boolean {
  return buf.length >= 8 && buf.subarray(0, 8).equals(PNG_SIGNATURE);
}

// Split a PNG into its ordered chunk list. Returns null if `buf` isn't a PNG.
function splitChunks(buf: Buffer): PngChunk[] | null {
  if (!isPng(buf)) return null;
  const chunks: PngChunk[] = [];
  let offset = 8; // skip signature
  let sawIend = false;
  while (offset + 8 <= buf.length) {
    const length = buf.readUInt32BE(offset);
    const type = buf.toString('ascii', offset + 4, offset + 8);
    const dataStart = offset + 8;
    const dataEnd = dataStart + length;
    if (dataEnd + 4 > buf.length) return null; // truncated — fail fast
    chunks.push({ type, data: buf.subarray(dataStart, dataEnd) });
    offset = dataEnd + 4; // advance past the 4-byte CRC
    if (type === 'IEND') {
      sawIend = true;
      break;
    }
  }
  return sawIend ? chunks : null;
}

// Re-assemble chunks into a PNG buffer, recomputing each chunk's CRC. CRCs over
// unchanged chunk data are identical to the originals, so untouched chunks
// (notably IDAT) round-trip byte-for-byte.
function assembleChunks(chunks: PngChunk[]): Buffer {
  const parts: Buffer[] = [PNG_SIGNATURE];
  for (const { type, data } of chunks) {
    const length = Buffer.alloc(4);
    length.writeUInt32BE(data.length, 0);
    const typeBuf = Buffer.from(type, 'ascii');
    const crcBuf = Buffer.alloc(4);
    crcBuf.writeUInt32BE(crc32(Buffer.concat([typeBuf, data])), 0);
    parts.push(length, typeBuf, data, crcBuf);
  }
  return Buffer.concat(parts);
}

// Decode a `tEXt` payload → { keyword, text }. Format: keyword (Latin-1), a 0x00
// separator, then the text. A1111 'parameters' is ASCII-ish but prompts can hold
// unicode, so the value is read as UTF-8.
function decodeText(data: Buffer): { keyword: string; text: string } | null {
  const nul = data.indexOf(0);
  if (nul === -1) return null;
  return {
    keyword: data.toString('latin1', 0, nul),
    text: data.toString('utf8', nul + 1),
  };
}

function encodeText(keyword: string, text: string): PngChunk {
  return {
    type: 'tEXt',
    data: Buffer.concat([
      Buffer.from(keyword, 'latin1'),
      Buffer.from([0]),
      Buffer.from(text, 'utf8'),
    ]),
  };
}

function isParametersKeyword(keyword: string | undefined | null): boolean {
  return typeof keyword === 'string' && PARAMETERS_KEYWORDS.has(keyword);
}

/** Read the A1111-style 'parameters' tEXt string. null if absent or not a PNG. */
export function readPngParameters(buf: Buffer): string | null {
  const chunks = splitChunks(buf);
  if (!chunks) return null;
  for (const c of chunks) {
    if (c.type !== 'tEXt') continue;
    const decoded = decodeText(c.data);
    if (decoded && isParametersKeyword(decoded.keyword)) return decoded.text;
  }
  return null;
}

/**
 * Replace (or insert) the 'parameters' tEXt chunk with `edited`, leaving every
 * other chunk — including all pixel data — byte-for-byte identical. Throws if
 * `buf` isn't a valid PNG.
 */
export function writePngParameters(buf: Buffer, edited: string): Buffer {
  const chunks = splitChunks(buf);
  if (!chunks) throw new Error('Not a valid PNG file');

  // Drop any existing 'parameters' tEXt chunk(s) before re-inserting.
  const kept = chunks.filter(
    (c) => c.type !== 'tEXt' || !isParametersKeyword(decodeText(c.data)?.keyword),
  );

  // tEXt must sit before IEND — insert right before it (append if IEND is absent).
  const iendIndex = kept.findIndex((c) => c.type === 'IEND');
  const newChunk = encodeText('parameters', edited);
  if (iendIndex === -1) kept.push(newChunk);
  else kept.splice(iendIndex, 0, newChunk);

  return assembleChunks(kept);
}
