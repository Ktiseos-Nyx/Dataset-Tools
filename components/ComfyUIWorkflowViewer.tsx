'use client';

import { useEffect, useRef, useState } from 'react';
// ComfyUIWorkflowViewer.tsx
import { LGraph, LGraphCanvas, LGraphNode, LiteGraph } from 'litegraph.js';
import 'litegraph.js/css/litegraph.css';
import { AlertCircle } from 'lucide-react';

interface ComfyUIWorkflowViewerProps {
  workflow: Record<string, any>;
  readOnly?: boolean;
  className?: string;
}

export function ComfyUIWorkflowViewer({ 
  workflow, 
  readOnly = true,
  className = ''
}: ComfyUIWorkflowViewerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!canvasRef.current || !workflow?.nodes) {
      setIsLoading(false);
      return;
    }

    const canvas = canvasRef.current;
	const rect = canvas.getBoundingClientRect();
	canvas.width = rect.width || 800;
    canvas.height = rect.height || 400;
    const graph = new LGraph();
    const graphCanvas = new LGraphCanvas(canvas, graph, {
      readOnly,
      skip_events: readOnly,
      skip_links: readOnly,
      autoresize: true,
    });

    // Minimal node registry — creates placeholder nodes for any type
    function registerMinimalNode(type: string) {
      if (LiteGraph.registered_node_types[type]) return;
      
      class MinimalNode extends LGraphNode {
        constructor() {
          super();
          this.title = type.split('/').pop() || type;
          this.addInput('', '*');
          this.addOutput('', '*');
          this.size = [140, 60];
          // Basic color coding by type category
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

    // Register all node types found in workflow
    for (const node of workflow.nodes) {
      if (node.type) registerMinimalNode(node.type);
    }

    // Load and render
    try {
      graph.load(workflow);
      graph.start();
      graphCanvas.draw();
      graphCanvas.ds.offset = [0, 0];
	  graphCanvas.ds.scale = 1;
      graphCanvas.setDirty(true, true);
    } catch (e) {
      console.error('Workflow render error:', e);
      setError('Could not render workflow graph');
    } finally {
      setIsLoading(false);
    }

    // Cleanup
    return () => {
  graph.stop();
};
  }, [workflow, readOnly]);

  if (isLoading) {
    return (
      <div className={`w-full h-[400px] bg-zinc-900/50 rounded-lg border border-zinc-700 flex items-center justify-center ${className}`}>
        <span className="text-xs text-zinc-400">Loading workflow graph...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`w-full p-3 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-2 ${className}`}>
        <AlertCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
        <p className="text-xs text-red-300">{error}</p>
      </div>
    );
  }

  if (!workflow?.nodes || workflow.nodes.length === 0) {
    return (
      <div className={`w-full p-4 text-center text-xs text-zinc-500 ${className}`}>
        No workflow graph data available
      </div>
    );
  }

  return (
    <div className={`relative w-full h-[400px] bg-zinc-900 rounded-lg border border-zinc-700 overflow-hidden ${className}`}>
      <canvas ref={canvasRef} className="w-full h-full" />
      {readOnly && (
        <div className="absolute top-2 right-2 px-2 py-1 text-[10px] bg-black/50 text-zinc-400 rounded border border-zinc-700">
          Read-only preview
        </div>
      )}
    </div>
  );
}