"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useDashboardStore } from "@/store/dashboard";
import { modelMetrics } from "@/lib/network-data";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip as RechartsTooltip, Cell,
  PieChart, Pie, Cell as PieCell
} from "recharts";
import {
  Shield, Zap, AlertTriangle, CheckCircle2, Clock, Database,
  FileText, GitBranch, Cpu, Network
} from "lucide-react";

const severityDistribution = [
  { name: "None", value: 2840, color: "#10b981" },
  { name: "Minor", value: 620, color: "#06b6d4" },
  { name: "Moderate", value: 380, color: "#f59e0b" },
  { name: "Severe", value: 145, color: "#f97316" },
  { name: "Critical", value: 41, color: "#ef4444" },
];

const riskByArea = [
  { area: "Area 1", avgRisk: 0.35, highRisk: 12, contingencies: 890 },
  { area: "Area 2", avgRisk: 0.42, highRisk: 18, contingencies: 1200 },
  { area: "Area 3", avgRisk: 0.51, highRisk: 24, contingencies: 1560 },
];

const pipelineSteps = [
  { step: 1, label: "Data Ingestion", desc: "Fetch NESO demand snapshot via CKAN API", icon: Database, status: "complete" },
  { step: 2, label: "Case Mapping", desc: "Scale GB demand onto IEEE 39-bus synthetic case", icon: Network, status: "complete" },
  { step: 3, label: "Feature Extraction", desc: "Compute 15 graph & operating features per contingency", icon: Cpu, status: "complete" },
  { step: 4, label: "ML Prediction", desc: "Random Forest risk scoring with grouped CV", icon: Brain, status: "complete" },
  { step: 5, label: "Conditional Screening", desc: "Rank & filter contingencies by risk threshold", icon: Shield, status: "complete" },
  { step: 6, label: "Mitigation Planning", desc: "Agent-based control action optimization", icon: Zap, status: "active" },
];

function Brain(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}>
      <path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z" />
      <path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z" />
      <path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4" />
      <path d="M17.599 6.5a3 3 0 0 0 .399-1.375" />
      <path d="M6.003 5.125A3 3 0 0 0 6.401 6.5" />
      <path d="M3.477 10.896a4 4 0 0 1 .585-.396" />
      <path d="M19.938 10.5a4 4 0 0 1 .585.396" />
      <path d="M6 18a4 4 0 0 1-1.967-.516" />
      <path d="M19.967 17.484A4 4 0 0 1 18 18" />
    </svg>
  );
}

export function OverviewDashboard() {
  const { branches, setActiveTab } = useDashboardStore();
  const totalScenarios = 5126;
  const highRiskCount = 54;
  const screenedCount = 312;

  return (
    <div className="space-y-4">
      {/* Key metrics row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Total Scenarios</p>
                <p className="text-2xl font-bold">{totalScenarios.toLocaleString()}</p>
                <p className="text-[10px] text-muted-foreground">N-1, N-2, N-3 contingencies</p>
              </div>
              <GitBranch className="h-5 w-5 text-violet-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Screened</p>
                <p className="text-2xl font-bold text-cyan-400">{screenedCount}</p>
                <p className="text-[10px] text-muted-foreground">ML threshold filtering</p>
              </div>
              <Shield className="h-5 w-5 text-cyan-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground">High Risk</p>
                <p className="text-2xl font-bold text-red-400">{highRiskCount}</p>
                <p className="text-[10px] text-muted-foreground">Score above 0.7 threshold</p>
              </div>
              <AlertTriangle className="h-5 w-5 text-red-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-muted-foreground">Model ROC AUC</p>
                <p className="text-2xl font-bold text-emerald-400">{modelMetrics.rocAuc.toFixed(4)}</p>
                <p className="text-[10px] text-muted-foreground">Random Forest, 5-fold CV</p>
              </div>
              <CheckCircle2 className="h-5 w-5 text-emerald-400 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Severity Distribution */}
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Cascade Severity Distribution
            </CardTitle>
          </CardHeader>
          <CardContent className="flex gap-4 items-center">
            <ResponsiveContainer width="55%" height={200}>
              <PieChart>
                <Pie data={severityDistribution} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value" strokeWidth={2} stroke="transparent">
                  {severityDistribution.map((entry, i) => (
                    <PieCell key={i} fill={entry.color} fillOpacity={0.85} />
                  ))}
                </Pie>
                <RechartsTooltip
                  contentStyle={{ backgroundColor: "rgba(15,23,42,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", fontSize: 11 }}
                  formatter={(v: number) => [`${v.toLocaleString()} scenarios`, ""]}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {severityDistribution.map(s => (
                <div key={s.name} className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: s.color }} />
                  <span className="text-xs flex-1">{s.name}</span>
                  <span className="text-xs font-mono text-muted-foreground">{s.value.toLocaleString()}</span>
                  <span className="text-[10px] text-muted-foreground w-12 text-right">{((s.value / totalScenarios) * 100).toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Risk by Area */}
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Risk Profile by Network Area
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={riskByArea} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <XAxis dataKey="area" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} />
                <YAxis tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} domain={[0, 1]} tickFormatter={(v) => (v * 100).toFixed(0) + "%"} />
                <RechartsTooltip
                  contentStyle={{ backgroundColor: "rgba(15,23,42,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", fontSize: 11 }}
                  formatter={(v: number, name: string) => [
                    name === "avgRisk" ? `${(v * 100).toFixed(1)}%` : v,
                    name === "avgRisk" ? "Avg Risk" : name === "highRisk" ? "High Risk Count" : "Contingencies"
                  ]}
                />
                <Bar dataKey="avgRisk" radius={[4, 4, 0, 0]}>
                  {riskByArea.map((d, i) => (
                    <Cell key={i} fill={d.avgRisk > 0.5 ? "#ef4444" : d.avgRisk > 0.35 ? "#f59e0b" : "#10b981"} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-3 gap-2 mt-3">
              {riskByArea.map(a => (
                <div key={a.area} className="bg-muted/50 rounded-lg p-2 text-center">
                  <p className="text-[10px] text-muted-foreground">{a.area}</p>
                  <p className="text-xs font-semibold">{a.contingencies.toLocaleString()} cont.</p>
                  <p className="text-[10px] text-red-400">{a.highRisk} high risk</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Steps */}
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Assessment Pipeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            {pipelineSteps.map((step, i) => (
              <div key={step.step} className="relative">
                {i < pipelineSteps.length - 1 && (
                  <div className={`hidden lg:block absolute top-5 left-[60%] w-[80%] h-px ${
                    step.status === "complete" ? "bg-emerald-500/40" : "bg-muted"
                  }`} />
                )}
                <div className={`rounded-lg border p-3 transition-all ${
                  step.status === "complete" ? "border-emerald-500/20 bg-emerald-500/5" :
                  step.status === "active" ? "border-cyan-500/30 bg-cyan-500/5" :
                  "border-border/30 bg-muted/20"
                }`}>
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`p-1.5 rounded ${
                      step.status === "complete" ? "bg-emerald-500/15" :
                      step.status === "active" ? "bg-cyan-500/15" : "bg-muted"
                    }`}>
                      <step.icon className={`h-3.5 w-3.5 ${
                        step.status === "complete" ? "text-emerald-400" :
                        step.status === "active" ? "text-cyan-400" : "text-muted-foreground"
                      }`} />
                    </div>
                    {step.status === "complete" && <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 ml-auto" />}
                    {step.status === "active" && <div className="ml-auto w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />}
                  </div>
                  <p className="text-xs font-medium">{step.label}</p>
                  <p className="text-[10px] text-muted-foreground mt-0.5 leading-tight">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Quick Navigation
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: "Network Topology", desc: "Interactive IEEE 39-bus graph", tab: "network" as const, icon: Network, color: "text-cyan-400" },
              { label: "Cascade Simulation", desc: "Step-through failure propagation", tab: "cascade" as const, icon: AlertTriangle, color: "text-red-400" },
              { label: "Model Performance", desc: "ROC, feature importance, CV scores", tab: "model" as const, icon: Brain, color: "text-emerald-400" },
              { label: "Mitigation Control", desc: "Agent-based intervention planning", tab: "mitigation" as const, icon: Shield, color: "text-amber-400" },
            ].map(item => (
              <button
                key={item.tab}
                onClick={() => setActiveTab(item.tab)}
                className="flex items-center gap-3 rounded-lg border border-border/50 p-3 text-left hover:bg-accent/50 transition-all hover:border-border"
              >
                <div className="p-2 rounded-lg bg-muted">
                  <item.icon className={`h-4 w-4 ${item.color}`} />
                </div>
                <div>
                  <p className="text-xs font-medium">{item.label}</p>
                  <p className="text-[10px] text-muted-foreground">{item.desc}</p>
                </div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}