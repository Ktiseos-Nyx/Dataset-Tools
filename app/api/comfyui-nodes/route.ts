import { NextResponse } from 'next/server';
import {
  lookupNode,
  classifyNodes,
  getRegistryStats,
  refreshRegistry,
  type NodeLookupResult,
} from '@/lib/comfyui-node-registry';
import {
  getGitHubSearchStats,
  isGitHubSearchAvailable,
  clearGitHubSearchCache,
} from '@/lib/comfyui-github-search';

/**
 * GET /api/comfyui-nodes?classType=KSampler
 * GET /api/comfyui-nodes?classTypes=KSampler,CLIPTextEncode,MyCustomNode
 * GET /api/comfyui-nodes?stats=true
 * GET /api/comfyui-nodes?refresh=true
 *
 * Add &github=true to any classType/classTypes lookup to enable the GitHub
 * code-search fallback for unknown nodes (requires GITHUB_TOKEN).
 *
 * Looks up ComfyUI node class_types against the extension-node-map registry.
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const useGitHubFallback = searchParams.get('github') === 'true';

  // Stats endpoint
  if (searchParams.get('stats') === 'true') {
    try {
      const [registry, github] = await Promise.all([
        getRegistryStats(),
        getGitHubSearchStats(),
      ]);
      return NextResponse.json({ ...registry, github });
    } catch (err) {
      return NextResponse.json({ error: 'Failed to get registry stats' }, { status: 500 });
    }
  }

  // Force refresh
  if (searchParams.get('refresh') === 'true') {
    try {
      await refreshRegistry();
      const stats = await getRegistryStats();
      return NextResponse.json({ refreshed: true, ...stats });
    } catch (err) {
      return NextResponse.json({ error: 'Failed to refresh registry' }, { status: 500 });
    }
  }

  // Batch lookup
  const classTypesParam = searchParams.get('classTypes');
  if (classTypesParam) {
    const types = classTypesParam.split(',').map(t => t.trim()).filter(Boolean);
    if (types.length === 0) {
      return NextResponse.json({ error: 'classTypes parameter is empty' }, { status: 400 });
    }
    if (types.length > 500) {
      return NextResponse.json({ error: 'Too many class types (max 500)' }, { status: 400 });
    }

    const results = await classifyNodes(types, { useGitHubFallback });
    return NextResponse.json(results);
  }

  // Single lookup
  const classType = searchParams.get('classType');
  if (classType) {
    const result = await lookupNode(classType, { useGitHubFallback });
    return NextResponse.json(result);
  }

  return NextResponse.json(
    { error: 'Provide ?classType=... or ?classTypes=... or ?stats=true' },
    { status: 400 }
  );
}

/**
 * POST /api/comfyui-nodes
 * Body: { workflow: { ... }, useGitHubFallback?: boolean }
 * Body: { clearGithubCache: true }
 *
 * Accepts a full ComfyUI workflow (API format) and classifies every node in it.
 * Returns a per-node classification with repo info where available.
 *
 * Set useGitHubFallback: true to enable the GitHub code-search fallback for
 * unknown nodes (requires GITHUB_TOKEN env var, configurable from Settings).
 *
 * Alternatively, send { clearGithubCache: true } to clear the GitHub search cache.
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();

    // Handle cache clearing
    if (body?.clearGithubCache === true) {
      try {
        await clearGitHubSearchCache();
        return NextResponse.json({ cleared: true });
      } catch (err) {
        return NextResponse.json({ error: 'Failed to clear github cache' }, { status: 500 });
      }
    }

    const workflow = body?.workflow;
    const useGitHubFallback = body?.useGitHubFallback === true;

    if (!workflow || typeof workflow !== 'object') {
      return NextResponse.json(
        { error: 'Request body must include a "workflow" object or "clearGithubCache" flag' },
        { status: 400 }
      );
    }

    // Extract unique class_types from the workflow
    const classTypes = new Set<string>();
    for (const nodeData of Object.values(workflow)) {
      const node = nodeData as any;
      if (node?.class_type) {
        classTypes.add(node.class_type);
      }
    }

    if (classTypes.size === 0) {
      return NextResponse.json({ error: 'No nodes with class_type found in workflow' }, { status: 400 });
    }

    const classifications = await classifyNodes([...classTypes], { useGitHubFallback });

    // Build summary counts
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

    return NextResponse.json({
      summary: {
        total: classTypes.size,
        builtin,
        custom,
        unknown,
        githubResolved,
      },
      githubFallbackUsed: useGitHubFallback && isGitHubSearchAvailable(),
      unknownNodes,
      classifications,
    });
  } catch (err) {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
}