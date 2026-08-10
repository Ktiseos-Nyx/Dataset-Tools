import { NextResponse } from 'next/server';
import { extractMetadataFromBuffer } from '../metadata/route';

export async function POST(request: Request) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;

    console.log('[metadata-from-file] received file:', file?.name, file?.type, file?.size);

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

    const diagnostics: string[] = [];

    if (file.type === 'image/png' || file.name.toLowerCase().endsWith('.png')) {
      const sig = buffer.toString('hex', 0, 8);
      diagnostics.push(`PNG sig: ${sig}`);
      let offset = 8;
      let chunkIndex = 0;
      while (offset + 8 <= buffer.length && chunkIndex < 200) {
        const length = buffer.readUInt32BE(offset);
        const type = buffer.toString('ascii', offset + 4, offset + 8);
        if (offset + 12 + length > buffer.length) break;
        const data = buffer.slice(offset + 8, offset + 8 + length);
        if (type === 'eXIf') {
          diagnostics.push(`Found eXIf chunk at offset ${offset}, length=${length}`);
          const byteOrder = data.toString('ascii', 0, 2);
          diagnostics.push(`eXIf byteOrder: "${byteOrder}"`);
          const tiffMagic = byteOrder === 'II'
            ? data.readUInt16LE(2)
            : byteOrder === 'MM'
            ? data.readUInt16BE(2)
            : -1;
          diagnostics.push(`eXIf TIFF magic: 0x${tiffMagic.toString(16)}`);
        }
        offset += 12 + length;
        chunkIndex++;
      }
      if (!diagnostics.some(d => d.includes('eXIf'))) {
        diagnostics.push('No eXIf chunk found in PNG');
      }
    }

    return NextResponse.json({ ...metadata, _diagnostic: diagnostics });
  } catch (error) {
    console.error('Error processing dropped file:', error);
    return NextResponse.json(
      { error: 'Failed to process file' },
      { status: 500 }
    );
  }
}
