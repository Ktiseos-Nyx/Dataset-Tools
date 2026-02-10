import { NextResponse } from 'next/server';
import fs from 'fs/promises';
import path from 'path';

// Quick flat check - does this exact file exist in this directory?
async function checkDir(dir: string, fileName: string, fileSize: number): Promise<boolean> {
  try {
    const filePath = path.join(dir, fileName);
    const stats = await fs.stat(filePath);
    return stats.size === fileSize;
  } catch {
    return false;
  }
}

// List immediate subdirectories only (no recursion)
async function getSubDirs(dir: string): Promise<string[]> {
  try {
    const entries = await fs.readdir(dir, { withFileTypes: true });
    return entries
      .filter(e => e.isDirectory() && !e.name.startsWith('.') && !e.name.startsWith('$'))
      .map(e => path.join(dir, e.name));
  } catch {
    return [];
  }
}

// Get available drives on Windows
async function getDrives(): Promise<string[]> {
  const drives: string[] = [];
  for (const letter of 'CDEFGHIJKLMNOPQRSTUVWXYZ') {
    try {
      await fs.access(`${letter}:\\`);
      drives.push(`${letter}:\\`);
    } catch { /* doesn't exist */ }
  }
  return drives;
}

export async function POST(request: Request) {
  try {
    const { fileName, fileSize, lastFolder } = await request.json();

    if (!fileName) {
      return NextResponse.json({ error: 'fileName required' }, { status: 400 });
    }

    // 1. Check last known folder first (instant)
    if (lastFolder) {
      if (await checkDir(lastFolder, fileName, fileSize)) {
        return NextResponse.json({ folder: lastFolder });
      }
    }

    // 2. Check project directory (instant)
    const projectDir = path.resolve('.');
    if (await checkDir(projectDir, fileName, fileSize)) {
      return NextResponse.json({ folder: projectDir });
    }

    // 3. Check common user folders (fast - flat check only)
    const home = process.env.USERPROFILE || process.env.HOME || '';
    const quickPaths = [
      path.join(home, 'Pictures'),
      path.join(home, 'Desktop'),
      path.join(home, 'Downloads'),
      path.join(home, 'Documents'),
    ];
    for (const p of quickPaths) {
      if (await checkDir(p, fileName, fileSize)) {
        return NextResponse.json({ folder: p });
      }
    }

    // 4. Scan all drives - but only 2 levels deep, breadth-first
    //    This catches things like G:\SomeFolder\SubFolder\image.png
    const drives = await getDrives();

    for (const drive of drives) {
      // Level 0: drive root
      if (await checkDir(drive, fileName, fileSize)) {
        return NextResponse.json({ folder: drive });
      }

      // Level 1: immediate subdirs of drive
      const level1 = await getSubDirs(drive);
      for (const dir1 of level1) {
        if (await checkDir(dir1, fileName, fileSize)) {
          return NextResponse.json({ folder: dir1 });
        }
      }

      // Level 2: one more level deep
      for (const dir1 of level1) {
        const level2 = await getSubDirs(dir1);
        for (const dir2 of level2) {
          if (await checkDir(dir2, fileName, fileSize)) {
            return NextResponse.json({ folder: dir2 });
          }
        }
      }
    }

    return NextResponse.json({ folder: null });
  } catch (error) {
    console.error('Find file error:', error);
    return NextResponse.json({ error: 'Search failed' }, { status: 500 });
  }
}
