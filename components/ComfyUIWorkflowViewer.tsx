'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { LGraph, LGraphCanvas, LGraphNode, LiteGraph, type IWidget } from 'litegraph.js';
import 'litegraph.js/css/litegraph.css';
import { AlertCircle, Download, X, Circle } from 'lucide-react';

interface ApiNode {
  class_type?: string;
  inputs?: Record<string, unknown>;
}

interface SerializedLiteNode {
  id: number;
  type: string;
  pos: number[];
  size: number[];
  inputs: Array<{ name: string; type: string; link: number }>;
  outputs: Array<{ name: string; type: string; links: number[] }>;
  properties: Record<string, unknown>;
  widgets_values: unknown[];
}

interface ComfyUIWorkflowViewerProps {
  workflow: Record<string, unknown>;
  readOnly?: boolean;
  className?: string;
  fileName?: string;
}

interface SelectedNodeInfo {
  id: number;
  type: string;
  title: string;
  inputs: Array<{ name: string; type: string; link: number | null }>;
  outputs: Array<{ name: string; type: string; links: number[] }>;
  widgets: Array<{ name: string; value: unknown }>;
  properties: Record<string, unknown>;
  raw: Record<string, unknown> | null;
}

function isPromptApiFormat(data: Record<string, unknown>): boolean {
  if (Array.isArray(data.nodes)) return false;
  const keys = Object.keys(data);
  if (keys.length === 0) return false;
  return (
    keys.every(k => /^\d+$/.test(k)) &&
    Object.values(data).every(
      (v) => typeof v === 'object' && v !== null && 'class_type' in v
    )
  );
}

function convertPromptApiToLiteGraph(apiData: Record<string, unknown>): Record<string, unknown> {
  const entries = Object.entries(apiData);
  const nodesById: Record<number, SerializedLiteNode> = {};
  const links: [number, number, number, number, number, string][] = [];
  let nextLinkId = 1;

  const cols = Math.max(1, Math.ceil(Math.sqrt(entries.length)));

  entries.forEach(([key, nodeData], index) => {
    const node = nodeData as ApiNode;
    const id = parseInt(key, 10);
    nodesById[id] = {
      id,
      type: node.class_type || 'Unknown',
      pos: [(index % cols) * 280, Math.floor(index / cols) * 200],
      size: [220, 80],
      inputs: [],
      outputs: [{ name: 'out', type: '*', links: [] }],
      properties: { 'Node name for S&R': node.class_type || '' },
      widgets_values: [],
    };
  });

  entries.forEach(([key, nodeData]) => {
    const node = nodeData as ApiNode;
    const toNodeId = parseInt(key, 10);
    const target = nodesById[toNodeId];
    let inputSlot = 0;

    for (const [name, value] of Object.entries(node.inputs ?? {})) {
      if (
        Array.isArray(value) &&
        value.length === 2 &&
        (typeof value[0] === 'number' || (typeof value[0] === 'string' && /^\d+$/.test(value[0]))) &&
        typeof value[1] === 'number'
      ) {
        const fromNodeId = Number(value[0]);
        const fromSlot = value[1];
        const lid = nextLinkId++;
        links.push([lid, fromNodeId, fromSlot, toNodeId, inputSlot, '*']);
        target.inputs.push({ name, type: '*', link: lid });

        const srcNode = nodesById[fromNodeId];
        if (srcNode) {
          while (srcNode.outputs.length <= fromSlot) {
            srcNode.outputs.push({ name: 'out', type: '*', links: [] });
          }
          srcNode.outputs[fromSlot].links.push(lid);
        }
        inputSlot++;
      } else {
        target.widgets_values.push(value);
      }
    }
  });

  return {
    nodes: Object.values(nodesById),
    links,
    groups: [],
    config: {},
    extra: {},
    version: 0.4,
  };
}

function getNodeColor(type: string): { color: string; bgcolor: string } {
  const t = type.toLowerCase();
  if (t.includes('load') || t.includes('checkpoint')) return { color: '#4ade80', bgcolor: '#1a3a1a' };
  if (t.includes('save') || t.includes('preview')) return { color: '#fbbf24', bgcolor: '#3a2a0a' };
  if (t.includes('ksampler') || t.includes('sampler')) return { color: '#f87171', bgcolor: '#3a1a1a' };
  if (t.includes('clip') || t.includes('conditioning')) return { color: '#60a5fa', bgcolor: '#1a2a3a' };
  if (t.includes('vae')) return { color: '#c084fc', bgcolor: '#2a1a3a' };
  if (t.includes('upscale') || t.includes('image')) return { color: '#34d399', bgcolor: '#1a3a2a' };
  if (t.includes('latent') || t.includes('empty')) return { color: '#f472b6', bgcolor: '#3a1a2a' };
  if (t.includes('lora') || t.includes('model')) return { color: '#a78bfa', bgcolor: '#2a1a3a' };
  return { color: '#94a3b8', bgcolor: '#1e293b' };
}

type Status = 'loading' | 'empty' | 'ready' | 'error';

export function ComfyUIWorkflowViewer({
  workflow,
  readOnly = true,
  className = '',
  fileName,
}: ComfyUIWorkflowViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const graphCanvasRef = useRef<LGraphCanvas | null>(null);
  const graphDataRef = useRef<Record<string, unknown> | null>(null);
  const [status, setStatus] = useState<Status>('loading');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<SelectedNodeInfo | null>(null);

  const extractNodeInfo = useCallback((liteNode: LGraphNode): SelectedNodeInfo | null => {
    try {
      const rawId = liteNode.id;
      const graphData = graphDataRef.current;
      const raw: Record<string, unknown> | null =
        graphData && Array.isArray(graphData.nodes)
          ? ((graphData.nodes as Record<string, unknown>[]).find((n) => n.id === rawId) ?? null)
          : ((graphData?.[String(rawId)] as Record<string, unknown>) ?? null);

      const widgets = (liteNode as LGraphNode & { widgets?: IWidget[] }).widgets ?? [];

      return {
        id: rawId,
        type: liteNode.type || (typeof raw?.type === 'string' ? raw.type : 'Unknown'),
        title: liteNode.title || String(rawId),
        inputs: (liteNode.inputs ?? []).map((inp, i) => ({
          name: inp.name || `input_${i}`,
          type: typeof inp.type === 'string' ? inp.type : '*',
          link: inp.link ?? null,
        })),
        outputs: (liteNode.outputs ?? []).map((out, i) => ({
          name: out.name || `output_${i}`,
          type: typeof out.type === 'string' ? out.type : '*',
          links: out.links ?? [],
        })),
        widgets: widgets.map((w, i) => ({
          name: w.name || `param_${i}`,
          value: w.value ?? null,
        })),
        properties: liteNode.properties ?? {},
        raw,
      };
    } catch {
      return null;
    }
  }, []);

  const handleDownload = useCallback(() => {
    try {
      const json = JSON.stringify(workflow, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName ? `${fileName.replace(/\.[^.]+$/, '')}-workflow.json` : 'workflow.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      // ignore
    }
  }, [workflow, fileName]);

  useEffect(() => {
    if (!canvasRef.current || !workflow) {
      setStatus('empty');
      return;
    }

    const isApi = isPromptApiFormat(workflow);
    const graphData = isApi ? convertPromptApiToLiteGraph(workflow) : workflow;
    graphDataRef.current = isApi ? workflow : graphData;

    const nodes = graphData.nodes;
    if (!Array.isArray(nodes) || nodes.length === 0) {
      setStatus('empty');
      return;
    }

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width || 800;
    canvas.height = rect.height || 400;

    const graph = new LGraph();
    const graphCanvas = new LGraphCanvas(canvas, graph, { autoresize: true });
    graphCanvasRef.current = graphCanvas;
    if (readOnly) {
      (graphCanvas as LGraphCanvas & { read_only: boolean }).read_only = true;
    }

    function registerMinimalNode(type: string) {
      if (LiteGraph.registered_node_types[type]) return;

      const { color, bgcolor } = getNodeColor(type);
      class MinimalNode extends LGraphNode {
        constructor() {
          super();
          this.title = type.split('/').pop() || type;
          this.addInput('', '*');
          this.addOutput('', '*');
          this.size = [140, 60];
          this.color = color;
          this.bgcolor = bgcolor;
        }
      }
      MinimalNode.title = type;
      LiteGraph.registerNodeType(type, MinimalNode);
    }

    for (const node of nodes) {
      if (node.type) registerMinimalNode(node.type);
    }

    graphCanvas.onNodeSelected = (n: LGraphNode) => {
      const info = extractNodeInfo(n);
      setSelectedNode(info);
    };

    graphCanvas.onNodeDeselected = () => {
      setSelectedNode(null);
    };

    try {
      graph.configure(graphData);
      graph.start();
      graphCanvas.draw();
      graphCanvas.ds.offset = [0, 0];
      graphCanvas.ds.scale = 1;
      graphCanvas.setDirty(true, true);
      setStatus('ready');
    } catch (e) {
      console.error('Workflow render error:', e);
      setErrorMsg('Could not render workflow graph');
      setStatus('error');
    }

    return () => {
      graph.stop();
      graphCanvas.setGraph(null as unknown as LGraph);
      graphCanvasRef.current = null;
      graphDataRef.current = null;
      setSelectedNode(null);
    };
  }, [workflow, readOnly, extractNodeInfo]);

  return (
    <div
      className={`relative w-full h-[500px] bg-zinc-900 rounded-lg border border-zinc-700 overflow-hidden ${className}`}
    >
      <div className="flex h-full">
        {/* Main graph area */}
        <div className="flex-1 relative min-w-0">
          <canvas ref={canvasRef} className="w-full h-full" />

          {status === 'loading' && (
            <div className="absolute inset-0 flex items-center justify-center bg-zinc-900/90">
              <span className="text-xs text-zinc-400">Loading workflow graph...</span>
            </div>
          )}

          {status === 'empty' && (
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-xs text-zinc-500">No workflow graph data available</span>
            </div>
          )}

          {status === 'error' && (
            <div className="absolute inset-0 flex items-start gap-2 p-3 bg-red-500/10">
              <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
              <p className="text-xs text-red-300">{errorMsg}</p>
            </div>
          )}

          {status === 'ready' && (
            <>
              <button
                type="button"
                onClick={handleDownload}
                className="absolute top-2 right-2 z-10 flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] bg-black/70 hover:bg-black/90 text-zinc-300 hover:text-white rounded border border-zinc-600 hover:border-zinc-500 transition-colors"
                title="Download workflow JSON"
              >
                <Download className="w-3 h-3" />
                Download
              </button>

              {readOnly && (
                <div className="absolute top-2 left-2 px-2 py-1 text-[10px] bg-black/50 text-zinc-400 rounded border border-zinc-700">
                  Read-only preview
                </div>
              )}
            </>
          )}
        </div>

        {/* Node detail panel */}
        {selectedNode && (
          <div className="w-72 border-l border-zinc-700 bg-zinc-900/95 overflow-y-auto flex-shrink-0">
            <div className="sticky top-0 z-10 flex items-center justify-between px-3 py-2.5 border-b border-zinc-700 bg-zinc-900">
              <span className="text-xs font-semibold text-zinc-200 truncate max-w-[200px]">
                {selectedNode.title}
              </span>
              <button
                type="button"
                onClick={() => setSelectedNode(null)}
                aria-label="Close node details"
                className="p-0.5 rounded hover:bg-zinc-700 text-zinc-500 hover:text-zinc-300 transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            <div className="p-3 space-y-3 text-[12px]">
              {/* Node type badge */}
              <div>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-zinc-800 text-zinc-300 border border-zinc-700">
                  <Circle className="w-1.5 h-1.5" style={{ fill: getNodeColor(selectedNode.type).color, color: getNodeColor(selectedNode.type).color }} />
                  {selectedNode.type}
                </span>
              </div>

              {/* ID */}
              <div className="text-zinc-500">
                Node #{selectedNode.id}
              </div>

              {/* Inputs */}
              {selectedNode.inputs.length > 0 && (
                <div>
                  <h4 className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">Inputs</h4>
                  <div className="space-y-1">
                    {selectedNode.inputs.map((inp, i) => (
                      <div key={i} className="flex items-center justify-between text-zinc-400 bg-zinc-800/50 rounded px-2 py-1">
                        <span className="truncate max-w-[120px]">{inp.name}</span>
                        {inp.link !== null ? (
                          <span className="text-[10px] text-emerald-400 font-mono">link #{inp.link}</span>
                        ) : (
                          <span className="text-[10px] text-zinc-600">—</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Outputs */}
              {selectedNode.outputs.length > 0 && (
                <div>
                  <h4 className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">Outputs</h4>
                  <div className="space-y-1">
                    {selectedNode.outputs.map((out, i) => (
                      <div key={i} className="text-zinc-400 bg-zinc-800/50 rounded px-2 py-1">
                        {out.name}
                        {out.links.length > 0 && (
                          <span className="ml-2 text-[10px] text-blue-400">
                            → {out.links.length} connection{out.links.length > 1 ? 's' : ''}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Widgets / settings */}
              {selectedNode.widgets.length > 0 && (
                <div>
                  <h4 className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">Settings</h4>
                  <div className="space-y-1">
                    {selectedNode.widgets.map((w, i) => (
                      <div key={i} className="text-zinc-400 bg-zinc-800/50 rounded px-2 py-1 break-all">
                        <span className="text-zinc-600">{w.name}: </span>
                        <span className="text-zinc-300 font-mono">
                          {typeof w.value === 'string' ? w.value : JSON.stringify(w.value)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Properties */}
              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <div>
                  <h4 className="text-[10px] font-semibold uppercase tracking-wider text-zinc-500 mb-1.5">Properties</h4>
                  <div className="space-y-1">
                    {Object.entries(selectedNode.properties).map(([key, value]) => (
                      <div key={key} className="text-zinc-400 bg-zinc-800/50 rounded px-2 py-1 break-all">
                        <span className="text-zinc-600">{key}: </span>
                        <span className="text-zinc-300">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
