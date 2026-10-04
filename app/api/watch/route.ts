import { NextResponse } from 'next/server';
import { stat } from 'fs/promises';
import path from 'path';
import { watch, type FSWatcher } from 'chokidar';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

function isLoopbackHost(host: string): boolean {
  const hostname = host.split(':')[0].toLowerCase();
  return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]';
}

function originGuard(request: Request): string | null {
  const origin = request.headers.get('origin');
  const host = request.headers.get('host');
  if (host && !isLoopbackHost(host)) {
    return 'Access denied - non-loopback host';
  }
  if (origin) {
    try {
      const originUrl = new URL(origin);
      if (!isLoopbackHost(originUrl.hostname)) {
        return 'Access denied - cross-origin request';
      }
    } catch {
      return 'Access denied - invalid origin';
    }
  }
  return null;
}

// GET /api/watch?dir=<absolute path>
// Server-sent events: pushes `{ type: 'change' }` whenever anything inside `dir`
// changes, plus an initial `{ type: 'ready' }`. Watching lives here (in the
// Next.js server) rather than in the Electron main process so it's reusable by
// the desktop shell, a future CLI, and the web demo — and so Chokidar runs
// against the server's own node_modules instead of a dep-free main bundle.
// Only absolute, existing directories on the loopback are accepted.
export async function GET(request: Request) {
  const guardError = originGuard(request);
  if (guardError) {
    return NextResponse.json({ error: guardError }, { status: 403 });
  }

  const { searchParams } = new URL(request.url);
  const dir = searchParams.get('dir');

  if (!dir) {
    return NextResponse.json({ error: 'Directory path is required' }, { status: 400 });
  }
  if (!path.isAbsolute(dir)) {
    return NextResponse.json({ error: 'Directory path must be absolute' }, { status: 400 });
  }

  try {
    const dirStat = await stat(dir);
    if (!dirStat.isDirectory()) {
      return NextResponse.json({ error: 'Path is not a directory' }, { status: 400 });
    }
  } catch {
    return NextResponse.json({ error: 'Directory not found' }, { status: 404 });
  }

  const encoder = new TextEncoder();
  let watcher: FSWatcher | null = null;
  let heartbeat: ReturnType<typeof setInterval> | null = null;
  let cleanedUp = false;

  const cleanup = () => {
    if (cleanedUp) return;
    cleanedUp = true;
    if (heartbeat) {
      clearInterval(heartbeat);
      heartbeat = null;
    }
    if (watcher) {
      void watcher.close().catch(() => {});
      watcher = null;
    }
  };

  const stream = new ReadableStream({
    start(controller) {
      const send = (payload: unknown) => {
        try {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
        } catch {
          // stream already closed — drop the event
        }
      };

      watcher = watch(dir, { ignoreInitial: true });
      const refresh = () => send({ type: 'change' });
      watcher.on('add', refresh);
      watcher.on('change', refresh);
      watcher.on('unlink', refresh);
      watcher.on('addDir', refresh);
      watcher.on('unlinkDir', refresh);

      send({ type: 'ready' });

      // Keep the connection alive and detect dead clients (Next's abort signal
      // is reliable in standalone but can lag in dev).
      heartbeat = setInterval(() => {
        if (request.signal.aborted) {
          cleanup();
          try {
            controller.close();
          } catch {
            // ignore
          }
          return;
        }
        try {
          controller.enqueue(encoder.encode(': ping\n\n'));
        } catch {
          // ignore
        }
      }, 20_000);

      request.signal.addEventListener('abort', () => {
        cleanup();
        try {
          controller.close();
        } catch {
          // ignore
        }
      });
    },
    cancel() {
      cleanup();
    },
  });

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache, no-transform',
      Connection: 'keep-alive',
    },
  });
}
