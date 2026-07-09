"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useDashboardStore } from "@/store/dashboard";
import { sampleMitigationActions } from "@/lib/network-data";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from "recharts";
import {
  Battery, Zap, TrendingDown, DollarSign, Shield, CheckCircle2,
  BatteryCharging, Lightbulb, ArrowUpCircle
} from "lucide-react";

const policyComparison = [
  { policy: "No Control", unserved: 18.2, cost: 0, actions: 0 },
  { policy: "Centralised", unserved: 3.1, cost: 4820, actions: 8 },
  { policy: "Auction", unserved: 4.2, cost: 3150, actions: 6 },
  { policy: "Risk-Gated", unserved: 3.8, cost: 2890, actions: 5 },
];

const sensitivityData = [
  { name: "Full Portfolio", loadShed: 4.2, battery: 6.1, genRamp: 3.8, unserved: 3.1 },
  { name: "Half Battery", loadShed: 5.8, battery: 3.0, genRamp: 4.2, unserved: 4.8 },
  { name: "No Battery", loadShed: 8.5, battery: 0, genRamp: 5.5, unserved: 7.2 },
  { name: "Load Only", loadShed: 12.1, battery: 0, genRamp: 0, unserved: 11.5 },
];

export function MitigationPanel() {
  const { mitigationEnabled, setMitigationEnabled, mitigationActions, selectedContingency } = useDashboardStore();

  const totalPower = mitigationActions.reduce((s, a) => s + a.powerMW, 0);
  const totalCost = mitigationActions.reduce((s, a) => s + a.totalCost, 0);
  const totalOverloadReduction = mitigationActions.reduce((s, a) => s + a.overloadReduction, 0);

  const typeIcon = (type: string) => {
    switch (type) {
      case "load_shedding": return <Lightbulb className="h-4 w-4 text-amber-400" />;
      case "battery_discharge": return <BatteryCharging className="h-4 w-4 text-cyan-400" />;
      case "generator_ramp": return <ArrowUpCircle className="h-4 w-4 text-emerald-400" />;
      default: return <Zap className="h-4 w-4" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Toggle */}
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className={`p-2.5 rounded-lg ${mitigationEnabled ? "bg-emerald-500/15" : "bg-muted"}`}>
                <Shield className={`h-5 w-5 ${mitigationEnabled ? "text-emerald-400" : "text-muted-foreground"}`} />
              </div>
              <div>
                <p className="text-sm font-semibold">Mitigation Control</p>
                <p className="text-xs text-muted-foreground">
                  {mitigationEnabled
                    ? "Agent-based control active — simulating intervention actions"
                    : "Control disabled — viewing unmitigated cascade results"
                  }
                </p>
              </div>
            </div>
            <Switch checked={mitigationEnabled} onCheckedChange={setMitigationEnabled} />
          </div>
          {mitigationEnabled && (
            <div className="grid grid-cols-3 gap-3 mt-4">
              <div className="bg-muted/50 rounded-lg p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Total Action</p>
                <p className="text-lg font-bold text-cyan-400">{totalPower} MW</p>
              </div>
              <div className="bg-muted/50 rounded-lg p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Est. Cost</p>
                <p className="text-lg font-bold text-amber-400">£{totalCost.toLocaleString()}</p>
              </div>
              <div className="bg-muted/50 rounded-lg p-3 text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Overload Relief</p>
                <p className="text-lg font-bold text-emerald-400">{(totalOverloadReduction * 100).toFixed(0)}%</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Mitigation Actions Detail */}
      {mitigationEnabled && (
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Control Actions ({mitigationActions.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {mitigationActions.map((action, i) => (
                <div key={i} className="flex items-center gap-3 bg-muted/30 rounded-lg p-3 border border-border/30">
                  {typeIcon(action.type)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{action.busName}</span>
                      <Badge variant="outline" className="text-[9px]">
                        {action.type.replace("_", " ")}
                      </Badge>
                    </div>
                    <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                      <span>{action.powerMW} MW</span>
                      <span>£{action.costPerMW}/MW</span>
                      <span className="text-emerald-400">-{(action.overloadReduction * 100).toFixed(0)}% overload</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold">£{action.totalCost.toLocaleString()}</p>
                    <p className="text-[10px] text-muted-foreground">total cost</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Policy Comparison */}
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Control Policy Comparison
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={policyComparison} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
              <XAxis dataKey="policy" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} />
              <YAxis yAxisId="left" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} label={{ value: "Unserved %", angle: -90, position: "insideLeft", offset: 15, fill: "rgba(255,255,255,0.4)", fontSize: 10 }} />
              <YAxis yAxisId="right" orientation="right" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} label={{ value: "Cost £", angle: 90, position: "insideRight", offset: 15, fill: "rgba(255,255,255,0.4)", fontSize: 10 }} />
              <RechartsTooltip
                contentStyle={{ backgroundColor: "rgba(15,23,42,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", fontSize: 11 }}
              />
              <Bar yAxisId="left" dataKey="unserved" fill="#ef4444" fillOpacity={0.8} radius={[4, 4, 0, 0]} name="Unserved Load %" />
              <Bar yAxisId="right" dataKey="cost" fill="#06b6d4" fillOpacity={0.8} radius={[4, 4, 0, 0]} name="Cost (£)" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Portfolio Sensitivity */}
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Portfolio Sensitivity Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <RadarChart data={sensitivityData} cx="50%" cy="50%" outerRadius="70%">
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis dataKey="name" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} />
              <PolarRadiusAxis tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 9 }} />
              <Radar name="Load Shed (MW)" dataKey="loadShed" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.15} strokeWidth={2} />
              <Radar name="Battery (MW)" dataKey="battery" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.15} strokeWidth={2} />
              <Radar name="Gen Ramp (MW)" dataKey="genRamp" stroke="#10b981" fill="#10b981" fillOpacity={0.15} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
          <div className="flex justify-center gap-4 text-[10px] text-muted-foreground mt-1">
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-amber-500 inline-block" /> Load Shed</span>
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-cyan-500 inline-block" /> Battery</span>
            <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-emerald-500 inline-block" /> Gen Ramp</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
