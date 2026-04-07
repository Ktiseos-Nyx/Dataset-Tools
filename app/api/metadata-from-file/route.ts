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

    return NextResponse.json(metadata);
  } catch (error) {
    console.error('Error processing dropped file:', error);
    return NextResponse.json(
      { error: 'Failed to process file' },
      { status: 500 }
    );
  }
}
