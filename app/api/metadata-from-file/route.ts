import { NextResponse } from 'next/server';
import { extractMetadataFromBuffer } from '../metadata/route';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;

    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    const metadata = await extractMetadataFromBuffer(
      buffer,
      file.type,
      file.name,
      file.size,
      new Date(file.lastModified).toISOString(),
    );

    try {
      const diagnostics: string[] = [];
      const isPNG = file.type === 'image/png' || file.name.toLowerCase().endsWith('.png');

      if (isPNG) {
        diagnostics.push(`file.size=${file.size} buffer.length=${buffer.length}`);
        const sig = buffer.toString('hex', 0, Math.min(8, buffer.length));
        diagnostics.push(`PNG sig: ${sig}`);
        let offset = 8;
        let chunkIndex = 0;
        while (offset + 8 <= buffer.length && chunkIndex < 200) {
          const length = buffer.readUInt32BE(offset);
          const type = buffer.toString('ascii', offset + 4, offset + 8);
          if (offset + 12 + length > buffer.length) {
            diagnostics.push(`Chunk ${type} at offset ${offset}: length ${length} exceeds buffer (${buffer.length})`);
            break;
          }
          const data = buffer.slice(offset + 8, offset + 8 + length);
          if (type === 'eXIf') {
            diagnostics.push(`Found eXIf at offset ${offset}, dataLen=${length}`);
            if (data.length >= 2) {
              diagnostics.push(`eXIf first bytes hex: ${data.toString('hex', 0, Math.min(8, data.length))}`);
              const byteOrder = data.toString('ascii', 0, Math.min(2, data.length));
              diagnostics.push(`eXIf byteOrder: "${byteOrder}"`);
            }
          } else if (type === 'tEXt') {
            const nullIdx = data.indexOf(0);
            const key = nullIdx > 0 ? data.toString('latin1', 0, nullIdx) : '?';
            diagnostics.push(`tEXt key="${key}" at offset ${offset}`);
          } else if (type === 'iTXt') {
            const nullIdx = data.indexOf(0);
            const key = nullIdx > 0 ? data.toString('latin1', 0, nullIdx) : '?';
            diagnostics.push(`iTXt key="${key}" at offset ${offset}`);
          }
          offset += 12 + length;
          chunkIndex++;
        }
        if (!diagnostics.some(d => d.includes('eXIf'))) {
          diagnostics.push('No eXIf chunk found');
        }
      }

      return NextResponse.json({ ...metadata, _diagnostic: diagnostics });
    } catch (diagErr) {
      return NextResponse.json({
        ...metadata,
        _diagnostic: [`Diagnostic error: ${diagErr instanceof Error ? diagErr.message : String(diagErr)}`],
      });
    }
  } catch (error) {
    console.error('Error processing dropped file:', error);
    return NextResponse.json(
      { error: 'Failed to process file' },
      { status: 500 }
    );
  }
}
