import { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { Network, Node as NetworkNode } from '../api';
import { useNavigate } from 'react-router-dom';
import { ZoomIn, ZoomOut, Maximize2, ExternalLink, ShieldAlert, Cpu } from 'lucide-react';

interface GraphProps {
  network: Network;
  mainAccountId: string;
}

export default function AbuseRingGraph({ network, mainAccountId }: GraphProps) {
  const fgRef = useRef<any>(null);
  const navigate = useNavigate();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [selectedNode, setSelectedNode] = useState<NetworkNode | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.clientWidth,
        height: 560
      });
    }
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: 560
        });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const graphData = useMemo(() => {
    return {
      nodes: network.nodes.map(n => ({ ...n })),
      links: network.edges.map(e => ({ ...e }))
    };
  }, [network]);

  const paintNode = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const isTarget = node.id === mainAccountId;
    const isSelected = selectedNode && selectedNode.id === node.id;
    const isAccount = node.type === 'account';

    // Set colors
    let color = '#94a3b8';
    if (isTarget) color = '#ef4444'; // critical red
    else if (isAccount) {
      if (node.risk_level === 'CRITICAL') color = '#ef4444';
      else if (node.risk_level === 'HIGH') color = '#f97316';
      else if (node.risk_level === 'MEDIUM') color = '#eab308';
      else color = '#3b82f6';
    } else {
      if (node.entity_type === 'device') color = '#a855f7';
      else if (node.entity_type === 'ip') color = '#06b6d4';
      else if (node.entity_type === 'address') color = '#84cc16';
      else if (node.entity_type === 'payment') color = '#f43f5e';
    }

    const size = isTarget ? 7 : (isAccount ? 5 : 3.5);

    ctx.beginPath();
    
    if (isAccount) {
      // Draw solid circle for accounts
      ctx.arc(node.x, node.y, size, 0, 2 * Math.PI, false);
      ctx.fillStyle = color;
      ctx.fill();
      
      // Target account highlight (glow effect)
      if (isTarget) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, size + 3, 0, 2 * Math.PI, false);
        ctx.strokeStyle = 'rgba(239, 68, 68, 0.7)';
        ctx.lineWidth = 1.5;
        ctx.stroke();
      }

      // Selected node ring
      if (isSelected && !isTarget) {
        ctx.beginPath();
        ctx.arc(node.x, node.y, size + 3, 0, 2 * Math.PI, false);
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    } else {
      // Draw hollow square for entities
      ctx.rect(node.x - size, node.y - size, size * 2, size * 2);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.8;
      ctx.stroke();
      ctx.fillStyle = isSelected ? 'rgba(255, 255, 255, 0.2)' : 'transparent';
      ctx.fill();
    }

    // Always render labels for target and selected, or when zoomed in
    if (globalScale > 2.2 || isTarget || isSelected) {
      const label = isAccount ? node.id : `${node.entity_type}`;
      const fontSize = Math.max(10 / globalScale, 3);
      ctx.font = `${fontSize}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isTarget ? '#fca5a5' : isSelected ? '#ffffff' : 'rgba(255, 255, 255, 0.85)';
      ctx.fillText(label, node.x, node.y + size + (5 / globalScale));
    }
  }, [mainAccountId, selectedNode]);

  const handleZoomIn = () => {
    if (fgRef.current) {
      fgRef.current.zoom(fgRef.current.zoom() * 1.4, 300);
    }
  };

  const handleZoomOut = () => {
    if (fgRef.current) {
      fgRef.current.zoom(fgRef.current.zoom() / 1.4, 300);
    }
  };

  const handleFit = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 50);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      <div 
        ref={containerRef} 
        style={{ 
          position: 'relative',
          width: '100%', 
          height: '560px', 
          border: '1px solid var(--border-color)', 
          borderRadius: '0.5rem', 
          overflow: 'hidden', 
          backgroundColor: '#070b12' 
        }}
      >
        <ForceGraph2D
          ref={fgRef}
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          nodeCanvasObject={paintNode}
          nodePointerAreaPaint={(node: any, color, ctx) => {
            ctx.fillStyle = color;
            ctx.beginPath();
            ctx.arc(node.x, node.y, 8, 0, 2 * Math.PI, false);
            ctx.fill();
          }}
          linkColor={(link: any) => {
            if (link.type === 'transaction') return 'rgba(255, 255, 255, 0.35)';
            if (link.type === 'shared_device') return 'rgba(168, 85, 247, 0.7)';
            if (link.type === 'shared_ip') return 'rgba(6, 182, 212, 0.7)';
            if (link.type === 'shared_address') return 'rgba(132, 204, 22, 0.7)';
            if (link.type === 'shared_payment') return 'rgba(244, 63, 94, 0.7)';
            return 'rgba(255,255,255,0.2)';
          }}
          linkWidth={(link: any) => link.type === 'transaction' ? 1.6 : 1.2}
          linkLineDash={(link: any) => link.type === 'transaction' ? [] : [4, 4]}
          linkDirectionalArrowLength={(link: any) => link.type === 'transaction' ? 4 : 0}
          linkDirectionalArrowRelPos={1}
          onNodeClick={(node: any) => {
            setSelectedNode(node);
          }}
          cooldownTicks={120}
          onEngineStop={() => fgRef.current?.zoomToFit(400, 50)}
        />

        {/* Floating Zoom & Controls */}
        <div style={{ position: 'absolute', top: '1rem', right: '1rem', display: 'flex', flexDirection: 'column', gap: '0.375rem', zIndex: 10 }}>
          <button
            type="button"
            className="btn btn-outline"
            style={{ padding: '0.4rem', backgroundColor: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(4px)' }}
            onClick={handleZoomIn}
            title="Zoom In"
          >
            <ZoomIn size={16} />
          </button>
          <button
            type="button"
            className="btn btn-outline"
            style={{ padding: '0.4rem', backgroundColor: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(4px)' }}
            onClick={handleZoomOut}
            title="Zoom Out"
          >
            <ZoomOut size={16} />
          </button>
          <button
            type="button"
            className="btn btn-outline"
            style={{ padding: '0.4rem', backgroundColor: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(4px)' }}
            onClick={handleFit}
            title="Reset View / Fit Graph"
          >
            <Maximize2 size={16} />
          </button>
        </div>

        {/* Graph node & edge count overlay */}
        <div style={{ position: 'absolute', top: '1rem', left: '1rem', padding: '0.375rem 0.75rem', backgroundColor: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(4px)', borderRadius: '0.375rem', border: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
          {network.nodes.length} Nodes · {network.edges.length} Connections
        </div>
      </div>

      {/* Selected Node Forensic Inspector Panel */}
      {selectedNode && (
        <div 
          className="p-4 rounded border flex items-center justify-between gap-4 flex-wrap"
          style={{ 
            backgroundColor: 'var(--bg-surface-hover)', 
            borderColor: selectedNode.id === mainAccountId ? 'var(--color-critical)' : 'var(--border-color)' 
          }}
        >
          <div className="flex items-center gap-3">
            {selectedNode.type === 'account' ? (
              <ShieldAlert size={22} className={selectedNode.risk_level === 'CRITICAL' ? 'text-critical' : selectedNode.risk_level === 'HIGH' ? 'text-high' : 'text-low'} />
            ) : (
              <Cpu size={22} className="text-secondary" />
            )}
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-semibold text-sm">
                  {selectedNode.id}
                </span>
                <span className="badge badge-outline text-xs">
                  {selectedNode.type === 'account' ? 'ACCOUNT NODE' : `SHARED ${selectedNode.entity_type?.toUpperCase()}`}
                </span>
                {selectedNode.risk_level && (
                  <span className={`badge ${selectedNode.risk_level.toLowerCase()} text-xs`}>
                    {selectedNode.risk_level} (Score: {selectedNode.risk_score})
                  </span>
                )}
              </div>
              <p className="text-xs text-secondary mt-1">
                {selectedNode.type === 'account'
                  ? (selectedNode.id === mainAccountId
                      ? 'Current investigation focus account'
                      : `Connected account in the transaction & entity network`)
                  : `Shared entity binding multiple coordinated accounts together in this cluster`
                }
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {selectedNode.type === 'account' && selectedNode.id !== mainAccountId && (
              <button
                type="button"
                className="btn btn-primary"
                style={{ padding: '0.4rem 0.875rem', fontSize: '0.8125rem' }}
                onClick={() => navigate(`/investigation/${selectedNode.id}`)}
              >
                <ExternalLink size={14} />
                Pivot to this Account
              </button>
            )}
            <button
              type="button"
              className="btn btn-outline"
              style={{ padding: '0.4rem 0.75rem', fontSize: '0.8125rem' }}
              onClick={() => setSelectedNode(null)}
            >
              Clear
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
