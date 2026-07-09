"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { modelMetrics } from "@/lib/network-data";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip,
  ResponsiveContainer, BarChart, Bar, Cell, RadialBarChart, RadialBar, Legend
} from "recharts";
import {
  Target, TrendingUp, BarChart3, Brain, CheckCircle2, XCircle
} from "lucide-react";

function ConfusionMatrix() {
  const { tp, tn, fp, fn } = modelMetrics.confusionMatrix;
  const total = tp + tn + fp + fn;
  const data = [
    { label: "True Positive", value: tp, pct: ((tp / total) * 100).toFixed(1), color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
    { label: "True Negative", value: tn, pct: ((tn / total) * 100).toFixed(1), color: "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" },
    { label: "False Positive", value: fp, pct: ((fp / total) * 100).toFixed(1), color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
    { label: "False Negative", value: fn, pct: ((fn / total) * 100).toFixed(1), color: "bg-red-500/20 text-red-400 border-red-500/30" },
  ];

  return (
    <div className="grid grid-cols-2 gap-2">
      {data.map(d => (
        <div key={d.label} className={`rounded-lg border p-3 text-center ${d.color}`}>
          <p className="text-[10px] font-medium uppercase tracking-wider opacity-80">{d.label}</p>
          <p className="text-2xl font-bold mt-1">{d.value.toLocaleString()}</p>
          <p className="text-[10px] opacity-70">{d.pct}%</p>
        </div>
      ))}
    </div>
  );
}

export function ModelPerformance() {
  const rocData = modelMetrics.rocCurve;
  const diagonal = rocData.map(d => ({ fpr: d.fpr, tpr: d.fpr }));

  const metricCards = [
    { label: "ROC AUC", value: modelMetrics.rocAuc, icon: Target, color: "text-emerald-400" },
    { label: "PR AUC", value: modelMetrics.prAuc, icon: TrendingUp, color: "text-cyan-400" },
    { label: "Accuracy", value: modelMetrics.accuracy, icon: BarChart3, color: "text-violet-400" },
    { label: "F1 Score", value: modelMetrics.f1Score, icon: Brain, color: "text-amber-400" },
  ];

  return (
    <div className="space-y-4">
      {/* Metric summary cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {metricCards.map(m => (
          <Card key={m.label} className="border-border/50 bg-card/80 backdrop-blur-sm">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-muted-foreground">{m.label}</p>
                  <p className={`text-2xl font-bold ${m.color}`}>{m.value.toFixed(4)}</p>
                </div>
                <m.icon className={`h-5 w-5 ${m.color} opacity-50`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* ROC Curve */}
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              ROC Curve
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={rocData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                <XAxis dataKey="fpr" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} label={{ value: "False Positive Rate", position: "insideBottom", offset: -2, fill: "rgba(255,255,255,0.4)", fontSize: 10 }} />
                <YAxis tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} label={{ value: "True Positive Rate", angle: -90, position: "insideLeft", offset: 15, fill: "rgba(255,255,255,0.4)", fontSize: 10 }} domain={[0, 1]} />
                <RechartsTooltip
                  contentStyle={{ backgroundColor: "rgba(15,23,42,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", fontSize: 11 }}
                  labelFormatter={(v) => `FPR: ${v}`}
                  formatter={(v: number) => [`TPR: ${v.toFixed(3)}`, "Model"]}
                />
                <Line dataKey="tpr" stroke="#10b981" strokeWidth={2.5} dot={false} name="Model" />
                <Line dataKey="tpr" data={diagonal} stroke="rgba(255,255,255,0.2)" strokeWidth={1} strokeDasharray="5 5" dot={false} name="Random" />
              </LineChart>
            </ResponsiveContainer>
            <div className="flex items-center justify-center gap-4 mt-2 text-[10px] text-muted-foreground">
              <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-emerald-500 inline-block" /> Model (AUC=0.9847)</span>
              <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-white/20 inline-block border-dashed" /> Random</span>
            </div>
          </CardContent>
        </Card>

        {/* Confusion Matrix */}
        <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
              Confusion Matrix
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <ConfusionMatrix />
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Precision</p>
                <p className="text-lg font-bold text-emerald-400">{(modelMetrics.precision * 100).toFixed(2)}%</p>
              </div>
              <div className="text-center">
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Recall</p>
                <p className="text-lg font-bold text-cyan-400">{(modelMetrics.recall * 100).toFixed(2)}%</p>
              </div>
            </div>
            <div className="text-center">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">Cross-Validation Scores (5-fold)</p>
              <div className="flex gap-1.5 justify-center">
                {modelMetrics.crossValidationScores.map((score, i) => (
                  <div key={i} className="bg-muted rounded-md px-2 py-1 text-center">
                    <p className="text-xs font-mono font-semibold">{score.toFixed(4)}</p>
                    <p className="text-[9px] text-muted-foreground">Fold {i + 1}</p>
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Mean: {(modelMetrics.crossValidationScores.reduce((a, b) => a + b, 0) / modelMetrics.crossValidationScores.length).toFixed(4)} |
                Std: {(Math.sqrt(modelMetrics.crossValidationScores.reduce((s, v) => s + (v - modelMetrics.crossValidationScores.reduce((a, b) => a + b, 0) / modelMetrics.crossValidationScores.length) ** 2, 0) / modelMetrics.crossValidationScores.length)).toFixed(4)}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Feature Importance */}
      <Card className="border-border/50 bg-card/80 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">
            Feature Importance (Random Forest)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={modelMetrics.featureImportance} layout="vertical" margin={{ top: 0, right: 40, left: 140, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
              <XAxis type="number" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} domain={[0, 0.2]} tickFormatter={(v) => (v * 100).toFixed(0) + "%"} />
              <YAxis dataKey="feature" type="category" tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 10 }} width={130} />
              <RechartsTooltip
                contentStyle={{ backgroundColor: "rgba(15,23,42,0.95)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", fontSize: 11 }}
                formatter={(v: number) => [`${(v * 100).toFixed(2)}%`, "Importance"]}
              />
              <Bar dataKey="importance" radius={[0, 4, 4, 0]}>
                {modelMetrics.featureImportance.map((_, i) => (
                  <Cell key={i} fill={i < 3 ? "#10b981" : i < 6 ? "#06b6d4" : i < 10 ? "#8b5cf6" : "#64748b"} fillOpacity={0.8 - i * 0.03} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
