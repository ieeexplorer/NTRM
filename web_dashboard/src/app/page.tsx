"use client";

import { useEffect } from "react";
import { useDashboardStore, type ActiveTab } from "@/store/dashboard";
import { NetworkGraph } from "@/components/dashboard/network-graph";
import { MetricCards, CascadePlayer, ContingencyTable, NetworkControls } from "@/components/dashboard/metric-cards";
import { ModelPerformance } from "@/components/dashboard/model-performance";
import { MitigationPanel } from "@/components/dashboard/mitigation-panel";
import { OverviewDashboard } from "@/components/dashboard/overview";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  LayoutDashboard, Network, Zap, Brain, Shield, Github,
  AlertTriangle, Clock, Cpu
} from "lucide-react";

const tabs: { value: ActiveTab; label: string; icon: React.ElementType }[] = [
  { value: "overview", label: "Overview", icon: LayoutDashboard },
  { value: "network", label: "Network", icon: Network },
  { value: "cascade", label: "Cascade", icon: Zap },
  { value: "model", label: "ML Model", icon: Brain },
  { value: "mitigation", label: "Mitigation", icon: Shield },
];

export default function DashboardPage() {
  const { activeTab, setActiveTab, mitigationEnabled, setMitigationEnabled, branches, selectedContingency } = useDashboardStore();

  useEffect(() => {
    const requestedTab = new URLSearchParams(window.location.search).get("tab") as ActiveTab | null;
    if (requestedTab && tabs.some(tab => tab.value === requestedTab)) {
      setActiveTab(requestedTab);
    }
  }, [setActiveTab]);

  const trippedCount = branches.filter(b => b.status === "tripped").length;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border/40 backdrop-blur-xl bg-background/60">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-500 to-cyan-500 flex items-center justify-center">
                  <Network className="h-4 w-4 text-white" />
                </div>
                <div>
                  <h1 className="text-sm font-bold tracking-tight">NTRM Dashboard</h1>
                  <p className="text-[10px] text-muted-foreground -mt-0.5">Network Theory Resilience Metric</p>
                </div>
              </div>
              <Badge variant="outline" className="text-[9px] border-emerald-500/30 text-emerald-400 hidden sm:inline-flex">
                IEEE 39-Bus
              </Badge>
              <Badge variant="outline" className="text-[9px] border-cyan-500/30 text-cyan-400 hidden sm:inline-flex">
                Research v2.0
              </Badge>
            </div>
            <div className="flex items-center gap-3">
              {trippedCount > 0 && (
                <Badge variant="destructive" className="text-[10px] animate-pulse gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  {trippedCount} branches tripped
                </Badge>
              )}
              <div className="flex items-center gap-2">
                <Label htmlFor="mit-toggle" className="text-[10px] text-muted-foreground hidden sm:inline">Mitigation</Label>
                <Switch id="mit-toggle" checked={mitigationEnabled} onCheckedChange={setMitigationEnabled} className="scale-90" />
              </div>
              <a
                href="https://github.com/ieeexplorer/NTRM/tree/research-cascade-prediction"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 rounded-lg hover:bg-accent/50 transition-colors"
              >
                <Github className="h-4 w-4 text-muted-foreground" />
              </a>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-4">
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as ActiveTab)}>
            <TabsList className="bg-muted/50 backdrop-blur-sm border border-border/40 mb-4 h-10 p-1">
              {tabs.map(tab => (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  className="gap-1.5 text-xs data-[state=active]:bg-background data-[state=active]:shadow-sm h-8 px-3"
                >
                  <tab.icon className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">{tab.label}</span>
                </TabsTrigger>
              ))}
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="mt-0">
              <OverviewDashboard />
            </TabsContent>

            {/* Network Tab */}
            <TabsContent value="network" className="mt-0">
              <div className="space-y-4">
                <MetricCards />
                <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
                  <div className="xl:col-span-3">
                    <NetworkGraph />
                  </div>
                  <div className="space-y-4">
                    <NetworkControls />
                    <BranchLoadingChart />
                  </div>
                </div>
              </div>
            </TabsContent>

            {/* Cascade Tab */}
            <TabsContent value="cascade" className="mt-0">
              <div className="space-y-4">
                <MetricCards />
                <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                  <div className="xl:col-span-2 space-y-4">
                    <NetworkGraph />
                    <CascadePlayer />
                  </div>
                  <ContingencyTable />
                </div>
              </div>
            </TabsContent>

            {/* Model Tab */}
            <TabsContent value="model" className="mt-0">
              <ModelPerformance />
            </TabsContent>

            {/* Mitigation Tab */}
            <TabsContent value="mitigation" className="mt-0">
              <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
                <div className="xl:col-span-2">
                  <MitigationPanel />
                </div>
                <div className="space-y-4">
                  <ContingencyTable />
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border/30 mt-auto">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-3 flex items-center justify-between text-[10px] text-muted-foreground">
          <span>University of Sussex — NTRM Research Prototype</span>
          <span className="flex items-center gap-1.5">
            <Cpu className="h-3 w-3" />
            Random Forest · DC Power Flow · IEEE 39-Bus · {branches.length} branches · 10 generators
          </span>
        </div>
      </footer>
    </div>
  );
}

function BranchLoadingChart() {
  const { branches } = useDashboardStore();
  const sorted = [...branches].sort((a, b) => b.loading - a.loading).slice(0, 12);

  return (
    <div className="border border-border/50 rounded-xl bg-card/80 backdrop-blur-sm p-4">
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">Top 12 Branch Loading</p>
      <div className="space-y-1.5">
        {sorted.map(b => (
          <div key={b.id} className="flex items-center gap-2 text-xs">
            <span className="font-mono w-10 text-muted-foreground text-right">Br {b.id}</span>
            <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  b.status === "tripped" ? "bg-red-500/40" :
                  b.loading > 1 ? "bg-red-500" :
                  b.loading > 0.9 ? "bg-amber-500" :
                  b.loading > 0.8 ? "bg-yellow-500" :
                  "bg-emerald-500/70"
                }`}
                style={{ width: `${Math.min(100, b.loading * 100)}%` }}
              />
            </div>
            <span className={`font-mono w-12 text-right ${
              b.status === "tripped" ? "text-red-400" :
              b.loading > 0.9 ? "text-amber-400" : "text-muted-foreground"
            }`}>
              {b.status === "tripped" ? "TRIP" : `${(b.loading * 100).toFixed(0)}%`}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
