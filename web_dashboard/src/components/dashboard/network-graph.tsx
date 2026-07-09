"use client";

import { useEffect, useRef } from "react";
import { useDashboardStore } from "@/store/dashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from "@/components/ui/tooltip";

const WIDTH = 750;
const HEIGHT = 540;
const PADDING = 40;

function getBranchColor(loading: number, status: string, isSelected: boolean): string {
  if (status === "tripped") return "rgba(239, 68, 68, 0.3)";
  if (isSelected) return "rgba(99, 102, 241, 0.9)";
  if (loading > 1.0) return "rgba(239, 68, 68, 0.9)";
  if (loading > 0.9) return "rgba(249, 115, 22, 0.9)";
  if (loading > 0.8) return "rgba(234, 179, 8, 0.85)";
  if (loading > 0.6) return "rgba(34, 197, 94, 0.7)";
  return "rgba(148, 163, 184, 0.5)";
}

function getBranchWidth(loading: number, status: string): number {
  if (status === "tripped") return 1;
  return Math.max(1.5, Math.min(5, loading * 4));
}

function getBusColor(bus: { type: string; id: number }, trippedBuses: Set<number>, islandBuses: Map<number, number[]>): string {
  if (bus.type === "generator") return "rgba(16, 185, 129, 0.95)";
  if (bus.type === "load") return "rgba(251, 146, 60, 0.95)";

  // Check if bus is in an island
  for (const [idx] of islandBuses) {
    if (islandBuses.get(idx)?.includes(bus.id)) {
      return idx === 0 ? "rgba(239, 68, 68, 0.8)" : "rgba(249, 115, 22, 0.8)";
    }
  }
  return "rgba(148, 163, 184, 0.9)";
}

function getBusRadius(bus: { type: string }): number {
  if (bus.type === "generator") return 10;
  if (bus.type === "load") return 8;
  return 5;
}

function drawArrow(ctx: CanvasRenderingContext2D, fromX: number, fromY: number, toX: number, toY: number, size: number) {
  const angle = Math.atan2(toY - fromY, toX - fromX);
  ctx.beginPath();
  ctx.moveTo(toX, toY);
  ctx.lineTo(
    toX - size * Math.cos(angle - Math.PI / 6),
    toY - size * Math.sin(angle - Math.PI / 6)
  );
  ctx.lineTo(
    toX - size * Math.cos(angle + Math.PI / 6),
    toY - size * Math.sin(angle + Math.PI / 6)
  );
  ctx.closePath();
  ctx.fill();
}

export function NetworkGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { buses, branches, selectedBranchId, setSelectedBranchId, currentCascadeStep, cascadeSteps, showFlowDirection, showIslands } = useDashboardStore();
  const hoveredBranchRef = useRef<number | null>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const animFrameRef = useRef<number>(0);

  // Compute tripped buses and islands from cascade steps
  const trippedBuses = new Set<number>();
  const islandBuses = new Map<number, number[]>();

  if (cascadeSteps.length > 0 && currentCascadeStep > 0) {
    const step = cascadeSteps[Math.min(currentCascadeStep, cascadeSteps.length - 1)];
    if (step?.islands) {
      step.islands.forEach((island, idx) => {
        islandBuses.set(idx, island.buses);
        if (island.generation === 0) {
          island.buses.forEach(b => trippedBuses.add(b));
        }
      });
    }
  }

  const scaleAndDraw = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;
    canvas.width = WIDTH * dpr;
    canvas.height = HEIGHT * dpr;
    ctx.scale(dpr, dpr);
    canvas.style.width = "100%";
    canvas.style.height = "auto";

    // Clear
    ctx.fillStyle = "transparent";
    ctx.fillRect(0, 0, WIDTH, HEIGHT);

    // Compute scale
    const xs = buses.map(b => b.x);
    const ys = buses.map(b => b.y);
    const minX = Math.min(...xs) - 30;
    const maxX = Math.max(...xs) + 30;
    const minY = Math.min(...ys) - 30;
    const maxY = Math.max(...ys) + 30;
    const scaleX = (WIDTH - PADDING * 2) / (maxX - minX);
    const scaleY = (HEIGHT - PADDING * 2) / (maxY - minY);
    const scale = Math.min(scaleX, scaleY);
    const offsetX = PADDING + ((WIDTH - PADDING * 2) - (maxX - minX) * scale) / 2;
    const offsetY = PADDING + ((HEIGHT - PADDING * 2) - (maxY - minY) * scale) / 2;

    const sx = (x: number) => (x - minX) * scale + offsetX;
    const sy = (y: number) => (y - minY) * scale + offsetY;

    const busMap = new Map(buses.map(b => [b.id, b]));

    // Draw island backgrounds
    if (showIslands && islandBuses.size > 0) {
      islandBuses.forEach((busIds, idx) => {
        const colors = ["rgba(239, 68, 68, 0.08)", "rgba(249, 115, 22, 0.08)"];
        const islandBusObjs = busIds.map(id => busMap.get(id)!).filter(Boolean);
        if (islandBusObjs.length < 2) return;
        const cx = islandBusObjs.reduce((s, b) => s + sx(b.x), 0) / islandBusObjs.length;
        const cy = islandBusObjs.reduce((s, b) => s + sy(b.y), 0) / islandBusObjs.length;
        const maxDist = Math.max(...islandBusObjs.map(b => Math.sqrt((sx(b.x) - cx) ** 2 + (sy(b.y) - cy) ** 2))) + 40;
        ctx.beginPath();
        ctx.arc(cx, cy, maxDist, 0, Math.PI * 2);
        ctx.fillStyle = colors[idx % colors.length];
        ctx.fill();
        ctx.strokeStyle = idx === 0 ? "rgba(239, 68, 68, 0.3)" : "rgba(249, 115, 22, 0.3)";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
      });
    }

    // Draw branches
    branches.forEach(branch => {
      const fromBus = busMap.get(branch.from);
      const toBus = busMap.get(branch.to);
      if (!fromBus || !toBus) return;

      const x1 = sx(fromBus.x);
      const y1 = sy(fromBus.y);
      const x2 = sx(toBus.x);
      const y2 = sy(toBus.y);

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.strokeStyle = getBranchColor(branch.loading, branch.status, branch.id === selectedBranchId);
      ctx.lineWidth = getBranchWidth(branch.loading, branch.status);
      if (branch.status === "tripped") {
        ctx.setLineDash([4, 6]);
      } else if (branch.id === hoveredBranchRef.current || branch.id === selectedBranchId) {
        ctx.setLineDash([]);
        ctx.lineWidth = getBranchWidth(branch.loading, branch.status) + 2;
      } else {
        ctx.setLineDash([]);
      }
      ctx.stroke();
      ctx.setLineDash([]);

      // Flow direction arrow
      if (showFlowDirection && branch.status !== "tripped") {
        const midX = (x1 + x2) / 2;
        const midY = (y1 + y2) / 2;
        const angle = Math.atan2(y2 - y1, x2 - x1);
        const arrowSize = 6;
        ctx.fillStyle = getBranchColor(branch.loading, branch.status, branch.id === selectedBranchId);
        const dir = branch.flowDir === "reverse" ? Math.PI : 0;
        ctx.beginPath();
        ctx.moveTo(midX + arrowSize * Math.cos(angle + dir), midY + arrowSize * Math.sin(angle + dir));
        ctx.lineTo(midX - arrowSize * Math.cos(angle + dir - Math.PI / 3), midY - arrowSize * Math.sin(angle + dir - Math.PI / 3));
        ctx.lineTo(midX - arrowSize * Math.cos(angle + dir + Math.PI / 3), midY - arrowSize * Math.sin(angle + dir + Math.PI / 3));
        ctx.closePath();
        ctx.fill();
      }
    });

    // Draw buses
    buses.forEach(bus => {
      const x = sx(bus.x);
      const y = sy(bus.y);
      const r = getBusRadius(bus);
      const color = getBusColor(bus, trippedBuses, islandBuses);

      // Glow effect for generators
      if (bus.type === "generator") {
        ctx.beginPath();
        ctx.arc(x, y, r + 4, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(16, 185, 129, 0.15)";
        ctx.fill();
      }

      // Bus circle
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,0.5)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Bus label
      ctx.fillStyle = "rgba(255,255,255,0.85)";
      ctx.font = "9px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`${bus.id}`, x, y + 3);
    });
  };

  useEffect(() => {
    animFrameRef.current = requestAnimationFrame(scaleAndDraw);
    return () => cancelAnimationFrame(animFrameRef.current);
  });

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) * (WIDTH / rect.width);
    const my = (e.clientY - rect.top) * (HEIGHT / rect.height);

    const xs = buses.map(b => b.x);
    const ys = buses.map(b => b.y);
    const minX = Math.min(...xs) - 30;
    const maxX = Math.max(...xs) + 30;
    const minY = Math.min(...ys) - 30;
    const maxY = Math.max(...ys) + 30;
    const scaleX = (WIDTH - PADDING * 2) / (maxX - minX);
    const scaleY = (HEIGHT - PADDING * 2) / (maxY - minY);
    const scale = Math.min(scaleX, scaleY);
    const offX = PADDING + ((WIDTH - PADDING * 2) - (maxX - minX) * scale) / 2;
    const offY = PADDING + ((HEIGHT - PADDING * 2) - (maxY - minY) * scale) / 2;
    const sx = (x: number) => (x - minX) * scale + offX;
    const sy = (y: number) => (y - minY) * scale + offY;

    const busMap = new Map(buses.map(b => [b.id, b]));
    let closestBranch: number | null = null;
    let closestDist = 15;

    branches.forEach(branch => {
      const fromBus = busMap.get(branch.from);
      const toBus = busMap.get(branch.to);
      if (!fromBus || !toBus) return;
      const x1 = sx(fromBus.x), y1 = sy(fromBus.y);
      const x2 = sx(toBus.x), y2 = sy(toBus.y);
      const dist = pointToSegmentDist(mx, my, x1, y1, x2, y2);
      if (dist < closestDist) {
        closestDist = dist;
        closestBranch = branch.id;
      }
    });

    setSelectedBranchId(closestBranch);
  };

  const selectedBranch = branches.find(b => b.id === selectedBranchId);

  return (
    <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">IEEE 39-Bus Network Topology</CardTitle>
          <div className="flex gap-2 text-[10px]">
            <Badge variant="outline" className="gap-1 border-emerald-500/30 text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-500" /> Generator</Badge>
            <Badge variant="outline" className="gap-1 border-orange-500/30 text-orange-400"><span className="w-2 h-2 rounded-full bg-orange-500" /> Load</Badge>
            <Badge variant="outline" className="gap-1 border-red-500/30 text-red-400"><span className="w-2 h-2 rounded-full bg-red-500" /> Overloaded</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="relative p-2">
        <canvas
          ref={canvasRef}
          onClick={handleClick}
          className="w-full cursor-crosshair rounded-lg"
          style={{ aspectRatio: `${WIDTH}/${HEIGHT}` }}
        />
        {selectedBranch && (
          <TooltipProvider>
            <Tooltip open>
              <TooltipTrigger asChild>
                <div className="absolute bottom-4 left-4 right-4 bg-background/95 backdrop-blur-sm border border-border rounded-lg p-3 shadow-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-xs font-semibold">Branch {selectedBranch.id} (Bus {selectedBranch.from} → Bus {selectedBranch.to})</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        Flow: {selectedBranch.flowMW} MW | Rating: {selectedBranch.rateA} MVA | Loading: {(selectedBranch.loading * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">
                        R: {selectedBranch.r.toFixed(4)} | X: {selectedBranch.x.toFixed(4)} | B: {selectedBranch.b.toFixed(4)}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge variant={selectedBranch.status === "overloaded" ? "destructive" : selectedBranch.status === "tripped" ? "destructive" : "secondary"} className="text-[10px]">
                        {selectedBranch.status === "tripped" ? "TRIPPED" : selectedBranch.status === "overloaded" ? "OVERLOADED" : "NORMAL"}
                      </Badge>
                      <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${selectedBranch.loading > 1 ? "bg-red-500" : selectedBranch.loading > 0.8 ? "bg-amber-500" : "bg-emerald-500"}`}
                          style={{ width: `${Math.min(100, selectedBranch.loading * 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </TooltipTrigger>
              <TooltipContent>Click elsewhere to deselect</TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
        <div ref={tooltipRef} />
      </CardContent>
    </Card>
  );
}

function pointToSegmentDist(px: number, py: number, x1: number, y1: number, x2: number, y2: number): number {
  const dx = x2 - x1, dy = y2 - y1;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return Math.sqrt((px - x1) ** 2 + (py - y1) ** 2);
  let t = ((px - x1) * dx + (py - y1) * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));
  const projX = x1 + t * dx, projY = y1 + t * dy;
  return Math.sqrt((px - projX) ** 2 + (py - projY) ** 2);
}
