import { NextResponse } from 'next/server';
import {
  lookupNode,
  classifyNodes,
  getRegistryStats,
  refreshRegistry,
  type NodeLookupResult,
} from '@/lib/comfyui-node-registry';

/**
 * GET /api/comfyui-nodes?classType=KSampler
 * GET /api/comfyui-nodes?classTypes=KSampler,CLIPTextEncode,MyCustomNode
 * GET /api/comfyui-nodes?stats=true
 * GET /api/comfyui-nodes?refresh=true
 *
 * Looks up ComfyUI node class_types against the extension-node-map registry.
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  // Stats endpoint
  if (searchParams.get('stats') === 'true') {
    try {
      const stats = await getRegistryStats();
      return NextResponse.json(stats);
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

    const results = await classifyNodes(types);
    return NextResponse.json(results);
  }

  // Single lookup
  const classType = searchParams.get('classType');
  if (classType) {
    const result = await lookupNode(classType);
    return NextResponse.json(result);
  }

  return NextResponse.json(
    { error: 'Provide ?classType=... or ?classTypes=... or ?stats=true' },
    { status: 400 }
  );
}

/**
 * POST /api/comfyui-nodes
 * Body: { workflow: { ... } }
 *
 * Accepts a full ComfyUI workflow (API format) and classifies every node in it.
 * Returns a per-node classification with repo info where available.
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    const workflow = body?.workflow;

    if (!workflow || typeof workflow !== 'object') {
      return NextResponse.json(
        { error: 'Request body must include a "workflow" object' },
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

    const classifications = await classifyNodes([...classTypes]);

    // Build summary counts
    let builtin = 0, custom = 0, unknown = 0;
    const unknownNodes: string[] = [];
    for (const [ct, result] of Object.entries(classifications)) {
      switch (result.classification) {
        case 'builtin': builtin++; break;
        case 'custom': custom++; break;
        case 'unknown': unknown++; unknownNodes.push(ct); break;
      }
    }

    return NextResponse.json({
      summary: {
        total: classTypes.size,
        builtin,
        custom,
        unknown,
      },
      unknownNodes,
      classifications,
    });
  } catch (err) {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }
}
