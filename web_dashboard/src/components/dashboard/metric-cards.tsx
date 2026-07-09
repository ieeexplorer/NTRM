"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useDashboardStore } from "@/store/dashboard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Zap, Shield, Activity, TrendingUp, AlertTriangle, CheckCircle2,
  Play, Pause, SkipForward, SkipBack, RotateCcw, ChevronRight
} from "lucide-react";

export function MetricCards() {
  const { branches, selectedContingency, mitigationEnabled } = useDashboardStore();

  const totalGeneration = 8252;
  const totalLoad = 6254;
  const overloadedCount = branches.filter(b => b.loading > 0.8).length;
  const trippedCount = branches.filter(b => b.status === "tripped").length;
  const maxLoading = Math.max(...branches.filter(b => b.status !== "tripped").map(b => b.loading), 0);
  const systemRisk = selectedContingency ? selectedContingency.riskScore :
    Math.min(1, overloadedCount / branches.length * 3 + (trippedCount > 0 ? 0.3 : 0));

  const metrics = [
    {
      label: "System Generation",
      value: `${totalGeneration.toLocaleString()}`,
      unit: "MW",
      sublabel: "10 generators online",
      icon: Zap,
      color: "text-emerald-400",
      bgColor: "bg-emerald-500/10",
      borderColor: "border-emerald-500/20",
    },
    {
      label: "Total Demand",
      value: `${totalLoad.toLocaleString()}`,
      unit: "MW",
      sublabel: "19 load buses served",
      icon: Activity,
      color: "text-cyan-400",
      bgColor: "bg-cyan-500/10",
      borderColor: "border-cyan-500/20",
    },
    {
      label: "Overloaded Lines",
      value: `${overloadedCount}`,
      unit: `/ ${branches.length}`,
      sublabel: `Max loading: ${(maxLoading * 100).toFixed(0)}%`,
      icon: AlertTriangle,
      color: overloadedCount > 0 ? "text-amber-400" : "text-emerald-400",
      bgColor: overloadedCount > 0 ? "bg-amber-500/10" : "bg-emerald-500/10",
      borderColor: overloadedCount > 0 ? "border-amber-500/20" : "border-emerald-500/20",
    },
    {
      label: "System Risk Score",
      value: (systemRisk * 100).toFixed(1),
      unit: "%",
      sublabel: systemRisk > 0.8 ? "CRITICAL" : systemRisk > 0.5 ? "ELEVATED" : "NOMINAL",
      icon: systemRisk > 0.8 ? AlertTriangle : Shield,
      color: systemRisk > 0.8 ? "text-red-400" : systemRisk > 0.5 ? "text-amber-400" : "text-emerald-400",
      bgColor: systemRisk > 0.8 ? "bg-red-500/10" : systemRisk > 0.5 ? "bg-amber-500/10" : "bg-emerald-500/10",
      borderColor: systemRisk > 0.8 ? "border-red-500/20" : systemRisk > 0.5 ? "border-amber-500/20" : "border-emerald-500/20",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {metrics.map((m) => (
        <Card key={m.label} className={`border ${m.borderColor} ${m.bgColor} bg-card/80 backdrop-blur-sm`}>
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-xs font-medium text-muted-foreground">{m.label}</p>
                <div className="flex items-baseline gap-1">
                  <span className={`text-2xl font-bold tracking-tight ${m.color}`}>{m.value}</span>
                  <span className="text-xs text-muted-foreground">{m.unit}</span>
                </div>
                <p className="text-[10px] text-muted-foreground">{m.sublabel}</p>
              </div>
              <div className={`p-2 rounded-lg ${m.bgColor}`}>
                <m.icon className={`h-4 w-4 ${m.color}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function CascadePlayer() {
  const {
    cascadeSteps, currentCascadeStep, isCascadePlaying,
    setCurrentCascadeStep, setCascadePlaying, resetNetwork, selectContingency, selectedContingency
  } = useDashboardStore();

  if (!selectedContingency || cascadeSteps.length === 0) return null;

  const step = cascadeSteps[currentCascadeStep];
  const totalSteps = cascadeSteps.length - 1;

  const togglePlay = () => {
    if (isCascadePlaying) {
      setCascadePlaying(false);
      return;
    }
    setCascadePlaying(true);
    let s = currentCascadeStep;
    const interval = setInterval(() => {
      s++;
      if (s > totalSteps) {
        clearInterval(interval);
        setCascadePlaying(false);
        return;
      }
      setCurrentCascadeStep(s);
    }, 1200);
  };

  return (
    <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Cascade Simulation</CardTitle>
            <Badge variant={selectedContingency.cascadeSeverity === "critical" ? "destructive" : selectedContingency.cascadeSeverity === "severe" ? "destructive" : "secondary"} className="text-[10px]">
              {selectedContingency.cascadeSeverity.toUpperCase()}
            </Badge>
          </div>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => { resetNetwork(); selectContingency(null); }}>
              <RotateCcw className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Progress bar */}
        <div className="relative">
          <div className="flex items-center gap-1 mb-2">
            {cascadeSteps.map((s, i) => (
              <div key={i} className="flex items-center gap-1 flex-1">
                <button
                  onClick={() => { setCurrentCascadeStep(i); setCascadePlaying(false); }}
                  className={`flex-1 h-1.5 rounded-full transition-all ${
                    i <= currentCascadeStep
                      ? s.trippedBranches.length > 0
                        ? "bg-red-500"
                        : "bg-emerald-500"
                      : "bg-muted"
                  }`}
                />
                {i < cascadeSteps.length - 1 && (
                  <ChevronRight className="h-3 w-3 text-muted-foreground/50 flex-shrink-0" />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => { setCurrentCascadeStep(0); setCascadePlaying(false); }}>
            <SkipBack className="h-3.5 w-3.5" />
          </Button>
          <Button variant="default" size="icon" className="h-8 w-8" onClick={togglePlay}>
            {isCascadePlaying ? <Pause className="h-3.5 w-3.5" /> : <Play className="h-3.5 w-3.5" />}
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => { setCurrentCascadeStep(totalSteps); setCascadePlaying(false); }}>
            <SkipForward className="h-3.5 w-3.5" />
          </Button>
          <div className="ml-3 text-xs text-muted-foreground">
            Step {currentCascadeStep} of {totalSteps} — {step?.timestamp}
          </div>
        </div>

        {/* Step details */}
        {step && (
          <div className="bg-muted/50 rounded-lg p-3 space-y-2">
            <p className="text-sm">{step.description}</p>
            {step.trippedBranches.length > 0 && (
              <div className="flex gap-1.5 flex-wrap">
                {step.trippedBranches.map(id => (
                  <Badge key={id} variant="destructive" className="text-[10px]">Branch {id} tripped</Badge>
                ))}
              </div>
            )}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="bg-background rounded-md p-2 text-center">
                <p className="text-muted-foreground">Load Lost</p>
                <p className="font-semibold text-red-400">{step.totalLoadLost} MW</p>
              </div>
              <div className="bg-background rounded-md p-2 text-center">
                <p className="text-muted-foreground">Gen Lost</p>
                <p className="font-semibold text-amber-400">{step.totalGenerationLost} MW</p>
              </div>
              <div className="bg-background rounded-md p-2 text-center">
                <p className="text-muted-foreground">Islands</p>
                <p className="font-semibold">{step.islands.length}</p>
              </div>
            </div>
            {step.loadingChanges.length > 0 && (
              <div className="space-y-1">
                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">Loading Changes</p>
                <div className="max-h-24 overflow-y-auto space-y-1">
                  {step.loadingChanges.map(c => (
                    <div key={c.branchId} className="flex items-center gap-2 text-xs bg-background rounded px-2 py-1">
                      <span className="font-mono w-16">Br {c.branchId}</span>
                      <span className="text-muted-foreground">{(c.before * 100).toFixed(0)}%</span>
                      <span className="text-muted-foreground">→</span>
                      <span className={c.after > 1 ? "text-red-400 font-semibold" : "text-amber-400"}>
                        {(c.after * 100).toFixed(0)}%
                      </span>
                      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div className={`h-full rounded-full ${c.after > 1 ? "bg-red-500" : "bg-amber-500"}`} style={{ width: `${Math.min(100, c.after * 100)}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function ContingencyTable() {
  const { selectContingency, selectedContingency, mitigationEnabled } = useDashboardStore();

  const contingencies = [
    { id: "N1-15", initiatingOutage: [15], cascadeSeverity: "severe" as const, riskScore: 0.94, unservedFraction: 0.18, branchesTripped: 4, totalLoadLostMW: 650, mlProbability: 0.92, mitigated: true, mitigatedUnservedFraction: 0.04 },
    { id: "N1-6", initiatingOutage: [6], cascadeSeverity: "critical" as const, riskScore: 0.97, unservedFraction: 0.32, branchesTripped: 7, totalLoadLostMW: 1200, mlProbability: 0.96, mitigated: true, mitigatedUnservedFraction: 0.08 },
    { id: "N1-29", initiatingOutage: [29], cascadeSeverity: "moderate" as const, riskScore: 0.72, unservedFraction: 0.09, branchesTripped: 2, totalLoadLostMW: 320, mlProbability: 0.71, mitigated: true, mitigatedUnservedFraction: 0.02 },
    { id: "N1-3", initiatingOutage: [3], cascadeSeverity: "none" as const, riskScore: 0.08, unservedFraction: 0.0, branchesTripped: 0, totalLoadLostMW: 0, mlProbability: 0.05, mitigated: false },
    { id: "N1-1", initiatingOutage: [1], cascadeSeverity: "minor" as const, riskScore: 0.35, unservedFraction: 0.03, branchesTripped: 1, totalLoadLostMW: 110, mlProbability: 0.31, mitigated: false },
    { id: "N1-21", initiatingOutage: [21], cascadeSeverity: "moderate" as const, riskScore: 0.68, unservedFraction: 0.07, branchesTripped: 2, totalLoadLostMW: 250, mlProbability: 0.65, mitigated: true, mitigatedUnservedFraction: 0.01 },
    { id: "N1-34", initiatingOutage: [34], cascadeSeverity: "none" as const, riskScore: 0.05, unservedFraction: 0.0, branchesTripped: 0, totalLoadLostMW: 0, mlProbability: 0.03, mitigated: false },
    { id: "N1-46", initiatingOutage: [46], cascadeSeverity: "severe" as const, riskScore: 0.89, unservedFraction: 0.15, branchesTripped: 3, totalLoadLostMW: 520, mlProbability: 0.87, mitigated: true, mitigatedUnservedFraction: 0.05 },
    { id: "N2-6-15", initiatingOutage: [6, 15], cascadeSeverity: "critical" as const, riskScore: 0.99, unservedFraction: 0.45, branchesTripped: 11, totalLoadLostMW: 2100, mlProbability: 0.98, mitigated: true, mitigatedUnservedFraction: 0.15 },
    { id: "N2-3-29", initiatingOutage: [3, 29], cascadeSeverity: "severe" as const, riskScore: 0.91, unservedFraction: 0.21, branchesTripped: 5, totalLoadLostMW: 780, mlProbability: 0.89, mitigated: true, mitigatedUnservedFraction: 0.06 },
  ];

  return (
    <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Contingency Screening Results
          </CardTitle>
          <Badge variant="secondary" className="text-[10px]">{contingencies.length} contingencies</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="max-h-80 overflow-y-auto">
          <div className="space-y-1.5">
            {contingencies
              .sort((a, b) => b.riskScore - a.riskScore)
              .map((c) => (
              <button
                key={c.id}
                onClick={() => selectContingency(c as any)}
                className={`w-full text-left rounded-lg p-2.5 transition-all hover:bg-accent/50 ${
                  selectedContingency?.id === c.id ? "bg-accent border border-border" : "border border-transparent"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Badge variant={c.cascadeSeverity === "critical" || c.cascadeSeverity === "severe" ? "destructive" : c.cascadeSeverity === "moderate" ? "secondary" : "outline"} className="text-[10px] font-mono">
                      {c.id}
                    </Badge>
                    <span className="text-xs text-muted-foreground">Br {c.initiatingOutage.join(", ")}</span>
                    {c.mitigated && mitigationEnabled && (
                      <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {mitigationEnabled && c.mitigated && (
                      <div className="text-right">
                        <p className="text-[10px] text-muted-foreground">Mitigated</p>
                        <p className="text-xs font-semibold text-emerald-400">{(c.mitigatedUnservedFraction! * 100).toFixed(1)}%</p>
                      </div>
                    )}
                    <div className="text-right">
                      <p className="text-[10px] text-muted-foreground">ML Prob</p>
                      <p className="text-xs font-mono font-semibold">{(c.mlProbability * 100).toFixed(1)}%</p>
                    </div>
                    <div className="text-right w-16">
                      <p className="text-[10px] text-muted-foreground">Unserved</p>
                      <p className={`text-xs font-semibold ${c.unservedFraction > 0.2 ? "text-red-400" : c.unservedFraction > 0.05 ? "text-amber-400" : "text-muted-foreground"}`}>
                        {mitigationEnabled && c.mitigated ? (c.mitigatedUnservedFraction! * 100).toFixed(1) : (c.unservedFraction * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div className="w-20">
                      <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            c.riskScore > 0.9 ? "bg-red-500" : c.riskScore > 0.6 ? "bg-amber-500" : "bg-emerald-500"
                          }`}
                          style={{ width: `${c.riskScore * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function NetworkControls() {
  const { showIslands, setShowIslands, showFlowDirection, setShowFlowDirection, loadingThreshold, setLoadingThreshold } = useDashboardStore();

  return (
    <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Display Controls</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Label className="text-xs">Show Islands</Label>
          <Switch checked={showIslands} onCheckedChange={setShowIslands} />
        </div>
        <div className="flex items-center justify-between">
          <Label className="text-xs">Flow Direction</Label>
          <Switch checked={showFlowDirection} onCheckedChange={setShowFlowDirection} />
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs">Loading Threshold</Label>
            <span className="text-xs font-mono text-muted-foreground">{(loadingThreshold * 100).toFixed(0)}%</span>
          </div>
          <Slider
            value={[loadingThreshold * 100]}
            onValueChange={([v]) => setLoadingThreshold(v / 100)}
            max={100}
            min={50}
            step={5}
            className="w-full"
          />
        </div>
      </CardContent>
    </Card>
  );
}
