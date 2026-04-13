'use client';

import { useEffect, useRef, useState } from 'react';
import { LGraph, LGraphCanvas, LGraphNode, LiteGraph } from 'litegraph.js';
import 'litegraph.js/css/litegraph.css';
import { AlertCircle } from 'lucide-react';

interface ComfyUIWorkflowViewerProps {
  workflow: Record<string, any>;
  readOnly?: boolean;
  className?: string;
}

// True when the object is the API/prompt format: {"1": {class_type, inputs}, ...}
// rather than the LiteGraph/workflow format: {nodes: [...], links: [...]}
function isPromptApiFormat(data: Record<string, any>): boolean {
  if (Array.isArray(data.nodes)) return false;
  const keys = Object.keys(data);
  if (keys.length === 0) return false;
  return (
    keys.every(k => /^\d+$/.test(k)) &&
    Object.values(data).every(
      (v: any) => v && typeof v === 'object' && 'class_type' in v
    )
  );
}

// Convert the ComfyUI API/prompt format to a minimal LiteGraph-serialisable graph.
// API format:  { "1": { class_type, inputs: { field: value | [nodeId, outSlot] } }, ... }
// LiteGraph:   { nodes: [{id, type, pos, inputs, outputs, widgets_values}], links: [[id, from, fromSlot, to, toSlot, type]] }
function convertPromptApiToLiteGraph(apiData: Record<string, any>): Record<string, any> {
  const entries = Object.entries(apiData);
  const nodesById: Record<number, any> = {};
  const links: [number, number, number, number, number, string][] = [];
  let nextLinkId = 1;

  const cols = Math.max(1, Math.ceil(Math.sqrt(entries.length)));

  // First pass: create skeleton nodes
  entries.forEach(([key, nodeData], index) => {
    const id = parseInt(key, 10);
    nodesById[id] = {
      id,
      type: nodeData.class_type || 'Unknown',
      pos: [(index % cols) * 280, Math.floor(index / cols) * 200],
      size: [220, 80],
      inputs: [],
      outputs: [{ name: 'out', type: '*', links: [] }],
      properties: { 'Node name for S&R': nodeData.class_type || '' },
      widgets_values: [],
    };
  });

  // Second pass: resolve inputs — connections vs. widget values
  entries.forEach(([key, nodeData]) => {
    const toNodeId = parseInt(key, 10);
    const node = nodesById[toNodeId];
    let inputSlot = 0;

    for (const [name, value] of Object.entries(nodeData.inputs ?? {})) {
      if (
        Array.isArray(value) &&
        value.length === 2 &&
        typeof value[0] === 'number' &&
        typeof value[1] === 'number'
      ) {
        const [fromNodeId, fromSlot] = value as [number, number];
        const lid = nextLinkId++;
        links.push([lid, fromNodeId, fromSlot, toNodeId, inputSlot, '*']);
        node.inputs.push({ name, type: '*', link: lid });

        const srcNode = nodesById[fromNodeId];
        if (srcNode) {
          while (srcNode.outputs.length <= fromSlot) {
            srcNode.outputs.push({ name: 'out', type: '*', links: [] });
          }
          srcNode.outputs[fromSlot].links.push(lid);
        }
        inputSlot++;
      } else {
        node.widgets_values.push(value);
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

type Status = 'loading' | 'empty' | 'ready' | 'error';

export function ComfyUIWorkflowViewer({
  workflow,
  readOnly = true,
  className = '',
}: ComfyUIWorkflowViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [status, setStatus] = useState<Status>('loading');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    // Canvas must be in the DOM — we always render it, so this should always be set.
    if (!canvasRef.current || !workflow) {
      setStatus('empty');
      return;
    }

    const graphData = isPromptApiFormat(workflow)
      ? convertPromptApiToLiteGraph(workflow)
      : workflow;

    if (!Array.isArray(graphData.nodes) || graphData.nodes.length === 0) {
      setStatus('empty');
      return;
    }

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width || 800;
    canvas.height = rect.height || 400;

    const graph = new LGraph();
    const graphCanvas = new LGraphCanvas(canvas, graph, { autoresize: true } as any);
    if (readOnly) {
      (graphCanvas as any).read_only = true;
    }

    // Register placeholder nodes for every type found in the graph
    function registerMinimalNode(type: string) {
      if (LiteGraph.registered_node_types[type]) return;

      class MinimalNode extends LGraphNode {
        constructor() {
          super();
          this.title = type.split('/').pop() || type;
          this.addInput('', '*');
          this.addOutput('', '*');
          this.size = [140, 60];
          if (type.includes('Load')) this.color = '#3a7';
          else if (type.includes('Save')) this.color = '#fa3';
          else if (type.includes('Sampler')) this.color = '#f33';
          else if (type.includes('Conditioning')) this.color = '#33f';
          else this.color = '#777';
          this.bgcolor = '#222';
        }
      }
      MinimalNode.title = type;
      LiteGraph.registerNodeType(type, MinimalNode);
    }

    for (const node of graphData.nodes) {
      if (node.type) registerMinimalNode(node.type);
    }

    try {
      graph.configure(graphData as any);
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
    };
  }, [workflow, readOnly]);

  // The canvas element is always in the DOM so canvasRef is populated before the effect runs.
  // Loading / empty / error states are overlaid on top of it.
  return (
    <div
      className={`relative w-full h-[400px] bg-zinc-900 rounded-lg border border-zinc-700 overflow-hidden ${className}`}
    >
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

      {status === 'ready' && readOnly && (
        <div className="absolute top-2 right-2 px-2 py-1 text-[10px] bg-black/50 text-zinc-400 rounded border border-zinc-700">
          Read-only preview
        </div>
      )}
    </div>
  );
}
