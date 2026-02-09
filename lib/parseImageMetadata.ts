/**
 * Image Metadata Parser
 *
 * Extracts AI generation metadata from images (PNG, JPEG)
 * Supports: A1111/Civitai, ComfyUI, NovelAI formats
 */

interface ParsedMetadata {
  format: 'A1111/Civitai' | 'ComfyUI' | 'NovelAI' | 'A1111/Civitai (JPEG)' | 'ComfyUI (JPEG)';
  params: Record<string, string>;
  raw_text: string;
  workflow_text?: string;
}

/**
 * Parse A1111/Automatic1111/Civitai format metadata
 * Format: "prompt text\nNegative prompt: negative text\nSteps: 20, Sampler: Euler a, CFG scale: 7, ..."
 */
function parseA1111Metadata(text: string): Record<string, string> {
  const params: Record<string, string> = {};

  try {
    const parts = text.split('Steps: ');
    if (parts.length !== 2) {
      throw new Error('Invalid A1111 format: missing Steps');
    }

    const prompts = parts[0];
    const parameters = 'Steps: ' + parts[1];

    // Extract positive and negative prompts
    if (prompts.includes('Negative prompt: ')) {
      const promptParts = prompts.split('Negative prompt: ');
      params['Prompt'] = promptParts[0].trim();
      params['Negative Prompt'] = promptParts[1].trim();
    } else {
      params['Prompt'] = prompts.trim();
    }

    // Extract parameters (Steps, Sampler, CFG, etc.)
    const paramList = parameters.split(', ');
    for (const param of paramList) {
      const [key, ...valueParts] = param.split(': ');
      if (key && valueParts.length > 0) {
        params[key.trim()] = valueParts.join(': ').trim();
      }
    }
  } catch (error) {
    params['Error'] = `Failed to parse: ${error}`;
  }

  return params;
}

/**
 * Parse ComfyUI workflow metadata
 * Format: JSON with node IDs and their inputs
 */
function parseComfyUIMetadata(jsonText: string): Record<string, string> {
  const params: Record<string, string> = {};

  try {
    const data = JSON.parse(jsonText);

    // Extract key information from nodes
    for (const [nodeId, nodeData] of Object.entries(data)) {
      const node = nodeData as any;
      const inputs = node.inputs || {};
      const classType = node.class_type || '';

      // Extract text prompts
      if (inputs.text && typeof inputs.text === 'string') {
        params[`${classType} (${nodeId})`] = inputs.text;
      }

      // Extract checkpoint/model
      if (inputs.ckpt_name) {
        params[`Checkpoint (${nodeId})`] = inputs.ckpt_name;
      }

      // Extract common parameters
      if (inputs.seed || inputs.noise_seed) {
        params[`Seed (${nodeId})`] = String(inputs.seed || inputs.noise_seed);
      }
      if (inputs.steps) {
        params[`Steps (${nodeId})`] = String(inputs.steps);
      }
      if (inputs.cfg) {
        params[`CFG (${nodeId})`] = String(inputs.cfg);
      }
    }
  } catch (error) {
    params['Error'] = `Failed to parse ComfyUI JSON: ${error}`;
  }

  return params;
}

/**
 * Parse NovelAI metadata
 * Format: JSON in Comment field
 */
function parseNovelAIMetadata(jsonText: string): Record<string, string> {
  const params: Record<string, string> = {};

  try {
    const data = JSON.parse(jsonText);

    params['Prompt'] = data.prompt || '';
    params['Negative Prompt'] = data.uc || '';
    params['Steps'] = String(data.steps || '');
    params['Sampler'] = data.sampler || '';
    params['CFG scale'] = String(data.scale || '');
    params['Seed'] = String(data.seed || '');

    if (data.width && data.height) {
      params['Size'] = `${data.width}x${data.height}`;
    }
    if (data.Source) {
      params['Model'] = data.Source;
    }
  } catch (error) {
    params['Error'] = `Failed to parse NovelAI JSON: ${error}`;
  }

  return params;
}

/**
 * Read PNG text chunks using browser APIs
 */
async function readPNGMetadata(arrayBuffer: ArrayBuffer): Promise<ParsedMetadata | null> {
  const bytes = new Uint8Array(arrayBuffer);

  // PNG signature check
  if (bytes[0] !== 0x89 || bytes[1] !== 0x50 || bytes[2] !== 0x4E || bytes[3] !== 0x47) {
    return null;
  }

  const decoder = new TextDecoder('utf-8');
  let offset = 8; // Skip PNG signature

  const textChunks: Record<string, string> = {};

  // Read chunks
  while (offset < bytes.length) {
    const length = new DataView(bytes.buffer, offset, 4).getUint32(0);
    const type = decoder.decode(bytes.slice(offset + 4, offset + 8));
    const data = bytes.slice(offset + 8, offset + 8 + length);

    if (type === 'tEXt' || type === 'zTXt' || type === 'iTXt') {
      // Find null separator
      let nullIndex = 0;
      for (let i = 0; i < data.length; i++) {
        if (data[i] === 0) {
          nullIndex = i;
          break;
        }
      }

      const keyword = decoder.decode(data.slice(0, nullIndex));
      const value = decoder.decode(data.slice(nullIndex + 1));
      textChunks[keyword] = value;
    }

    offset += 12 + length; // length(4) + type(4) + data(length) + crc(4)

    if (type === 'IEND') break;
  }

  // Check for NovelAI
  if (textChunks['Software'] === 'NovelAI' && textChunks['Comment']) {
    return {
      format: 'NovelAI',
      params: parseNovelAIMetadata(textChunks['Comment']),
      raw_text: textChunks['Comment']
    };
  }

  // Check for A1111
  if (textChunks['parameters'] && textChunks['parameters'].includes('Steps:')) {
    return {
      format: 'A1111/Civitai',
      params: parseA1111Metadata(textChunks['parameters']),
      raw_text: textChunks['parameters']
    };
  }

  // Check for ComfyUI
  if (textChunks['prompt'] && textChunks['prompt'].trim().startsWith('{')) {
    return {
      format: 'ComfyUI',
      params: parseComfyUIMetadata(textChunks['prompt']),
      raw_text: textChunks['prompt'],
      workflow_text: textChunks['workflow']
    };
  }

  return null;
}

/**
 * Read JPEG EXIF data (for Civitai images)
 * Note: This is a simplified version - for production use exifr library
 */
async function readJPEGMetadata(arrayBuffer: ArrayBuffer): Promise<ParsedMetadata | null> {
  // For proper JPEG EXIF parsing, you should use the 'exifr' library
  // This is a basic implementation that looks for Civitai's UserComment field

  const bytes = new Uint8Array(arrayBuffer);

  // JPEG signature check
  if (bytes[0] !== 0xFF || bytes[1] !== 0xD8) {
    return null;
  }

  // Look for APP1 marker (EXIF)
  let offset = 2;
  while (offset < bytes.length - 1) {
    if (bytes[offset] === 0xFF && bytes[offset + 1] === 0xE1) {
      // Found APP1
      const length = (bytes[offset + 2] << 8) | bytes[offset + 3];
      const exifData = bytes.slice(offset + 4, offset + 2 + length);

      // Look for "UNICODE" prefix in the data (Civitai's UserComment format)
      const decoder = new TextDecoder('utf-8');
      const exifText = decoder.decode(exifData);

      if (exifText.includes('UNICODE')) {
        // Find the UNICODE marker
        const unicodeIndex = exifText.indexOf('UNICODE');
        if (unicodeIndex !== -1) {
          // Extract bytes after UNICODE\x00\x00
          const commentStart = offset + 4 + unicodeIndex + 8;
          let commentBytes = bytes.slice(commentStart, offset + 2 + length);

          // Strip null bytes (Civitai stores as UTF-16-LE with nulls)
          const strippedBytes = commentBytes.filter(b => b !== 0);
          const comment = decoder.decode(strippedBytes);

          // Check if it's ComfyUI JSON or A1111 text
          if (comment.trim().startsWith('{')) {
            return {
              format: 'ComfyUI (JPEG)',
              params: parseComfyUIMetadata(comment),
              raw_text: comment
            };
          } else if (comment.includes('Steps:')) {
            return {
              format: 'A1111/Civitai (JPEG)',
              params: parseA1111Metadata(comment),
              raw_text: comment
            };
          }
        }
      }
      break;
    }
    offset++;
  }

  return null;
}

/**
 * Main function to parse image metadata
 * Supports both PNG and JPEG formats
 */
export async function parseImageMetadata(file: File): Promise<ParsedMetadata | null> {
  const arrayBuffer = await file.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);

  // Detect file type
  const isPNG = bytes[0] === 0x89 && bytes[1] === 0x50 && bytes[2] === 0x4E && bytes[3] === 0x47;
  const isJPEG = bytes[0] === 0xFF && bytes[1] === 0xD8;

  if (isPNG) {
    return readPNGMetadata(arrayBuffer);
  } else if (isJPEG) {
    return readJPEGMetadata(arrayBuffer);
  }

  return null;
}

/**
 * Format metadata for display
 */
export function formatMetadataForDisplay(metadata: ParsedMetadata): string {
  let output = `Format: ${metadata.format}\n\n`;
  output += 'Parameters:\n';
  output += '='.repeat(80) + '\n\n';

  for (const [key, value] of Object.entries(metadata.params)) {
    output += `${key}:\n  ${value}\n\n`;
  }

  return output;
}
