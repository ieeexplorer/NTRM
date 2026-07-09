// IEEE 39-bus (New England) test system data
// Based on the standard IEEE 39-bus benchmark used in NTRM research

export interface Bus {
  id: number;
  name: string;
  type: "generator" | "load" | "junction";
  x: number;
  y: number;
  voltage: number;
  angle: number;
  generationMW: number;
  loadMW: number;
  area: number;
}

export interface Branch {
  id: number;
  from: number;
  to: number;
  r: number;
  x: number;
  b: number;
  rateA: number; // MVA rating
  loading: number; // 0-1+ ratio
  status: "normal" | "overloaded" | "tripped" | "selected";
  flowMW: number;
  flowDir: "forward" | "reverse";
}

export interface CascadeStep {
  step: number;
  timestamp: string;
  description: string;
  trippedBranches: number[];
  loadingChanges: { branchId: number; before: number; after: number }[];
  totalLoadLost: number;
  totalGenerationLost: number;
  islands: { buses: number[]; generation: number; load: number }[];
}

export interface ContingencyResult {
  id: string;
  initiatingOutage: number[];
  cascadeSeverity: "none" | "minor" | "moderate" | "severe" | "critical";
  riskScore: number;
  unservedFraction: number;
  branchesTripped: number;
  steps: CascadeStep[];
  totalLoadLostMW: number;
  mlProbability: number;
  mitigated: boolean;
  mitigatedUnservedFraction?: number;
}

export interface ModelMetrics {
  rocAuc: number;
  prAuc: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1Score: number;
  confusionMatrix: { tp: number; tn: number; fp: number; fn: number };
  rocCurve: { fpr: number; tpr: number }[];
  featureImportance: { feature: string; importance: number }[];
  crossValidationScores: number[];
}

export interface RiskAssessment {
  timestamp: string;
  systemRiskScore: number;
  demandMW: number;
  demandScale: number;
  totalBranches: number;
  overloadedBranches: number;
  screenedContingencies: number;
  highRiskContingencies: number;
  topRisks: ContingencyResult[];
}

export interface MitigationAction {
  busId: number;
  busName: string;
  type: "load_shedding" | "battery_discharge" | "generator_ramp";
  powerMW: number;
  costPerMW: number;
  totalCost: number;
  overloadReduction: number;
}

// IEEE 39-bus coordinates (arranged in a realistic layout)
export const buses: Bus[] = [
  { id: 1, name: "Bus 1", type: "generator", x: 480, y: 60, voltage: 1.0, angle: 0, generationMW: 1000, loadMW: 0, area: 1 },
  { id: 2, name: "Bus 2", type: "generator", x: 420, y: 120, voltage: 0.995, angle: -1.5, generationMW: 700, loadMW: 0, area: 1 },
  { id: 3, name: "Bus 3", type: "junction", x: 350, y: 100, voltage: 0.99, angle: -3.2, generationMW: 0, loadMW: 0, area: 1 },
  { id: 4, name: "Bus 4", type: "junction", x: 300, y: 170, voltage: 0.985, angle: -4.8, generationMW: 0, loadMW: 0, area: 1 },
  { id: 5, name: "Bus 5", type: "junction", x: 240, y: 130, voltage: 0.982, angle: -5.5, generationMW: 0, loadMW: 0, area: 1 },
  { id: 6, name: "Bus 6", type: "generator", x: 180, y: 80, voltage: 0.995, angle: -3.4, generationMW: 700, loadMW: 0, area: 2 },
  { id: 7, name: "Bus 7", type: "junction", x: 150, y: 170, voltage: 0.985, angle: -5.1, generationMW: 0, loadMW: 0, area: 2 },
  { id: 8, name: "Bus 8", type: "generator", x: 100, y: 110, voltage: 0.995, angle: -2.9, generationMW: 700, loadMW: 0, area: 2 },
  { id: 9, name: "Bus 9", type: "junction", x: 90, y: 210, voltage: 0.98, angle: -6.3, generationMW: 0, loadMW: 0, area: 2 },
  { id: 10, name: "Bus 10", type: "load", x: 50, y: 160, voltage: 0.978, angle: -6.9, generationMW: 0, loadMW: 250, area: 2 },
  { id: 11, name: "Bus 11", type: "load", x: 70, y: 280, voltage: 0.975, angle: -7.5, generationMW: 0, loadMW: 250, area: 2 },
  { id: 12, name: "Bus 12", type: "load", x: 170, y: 300, voltage: 0.977, angle: -7.1, generationMW: 0, loadMW: 200, area: 2 },
  { id: 13, name: "Bus 13", type: "junction", x: 280, y: 260, voltage: 0.98, angle: -5.9, generationMW: 0, loadMW: 0, area: 3 },
  { id: 14, name: "Bus 14", type: "load", x: 210, y: 370, voltage: 0.975, angle: -7.8, generationMW: 0, loadMW: 200, area: 3 },
  { id: 15, name: "Bus 15", type: "generator", x: 350, y: 350, voltage: 0.99, angle: -4.2, generationMW: 500, loadMW: 0, area: 3 },
  { id: 16, name: "Bus 16", type: "load", x: 100, y: 370, voltage: 0.976, angle: -7.9, generationMW: 0, loadMW: 200, area: 3 },
  { id: 17, name: "Bus 17", type: "load", x: 380, y: 430, voltage: 0.974, angle: -8.2, generationMW: 0, loadMW: 200, area: 3 },
  { id: 18, name: "Bus 18", type: "generator", x: 460, y: 350, voltage: 0.99, angle: -4.0, generationMW: 500, loadMW: 0, area: 3 },
  { id: 19, name: "Bus 19", type: "load", x: 520, y: 280, voltage: 0.978, angle: -6.5, generationMW: 0, loadMW: 300, area: 1 },
  { id: 20, name: "Bus 20", type: "junction", x: 550, y: 200, voltage: 0.983, angle: -5.2, generationMW: 0, loadMW: 0, area: 1 },
  { id: 21, name: "Bus 21", type: "load", x: 620, y: 240, voltage: 0.977, angle: -6.6, generationMW: 0, loadMW: 274, area: 1 },
  { id: 22, name: "Bus 22", type: "load", x: 670, y: 170, voltage: 0.976, angle: -6.8, generationMW: 0, loadMW: 250, area: 1 },
  { id: 23, name: "Bus 23", type: "load", x: 680, y: 100, voltage: 0.978, angle: -6.2, generationMW: 0, loadMW: 300, area: 1 },
  { id: 24, name: "Bus 24", type: "junction", x: 600, y: 60, voltage: 0.982, angle: -4.5, generationMW: 0, loadMW: 0, area: 1 },
  { id: 25, name: "Bus 25", type: "junction", x: 530, y: 130, voltage: 0.984, angle: -4.8, generationMW: 0, loadMW: 0, area: 1 },
  { id: 26, name: "Bus 26", type: "junction", x: 460, y: 180, voltage: 0.983, angle: -5.0, generationMW: 0, loadMW: 0, area: 1 },
  { id: 27, name: "Bus 27", type: "junction", x: 390, y: 220, voltage: 0.981, angle: -5.3, generationMW: 0, loadMW: 0, area: 3 },
  { id: 28, name: "Bus 28", type: "generator", x: 300, y: 320, voltage: 0.99, angle: -4.5, generationMW: 400, loadMW: 0, area: 3 },
  { id: 29, name: "Bus 29", type: "load", x: 240, y: 220, voltage: 0.979, angle: -6.0, generationMW: 0, loadMW: 250, area: 2 },
  { id: 30, name: "Bus 30", type: "load", x: 140, y: 240, voltage: 0.978, angle: -6.5, generationMW: 0, loadMW: 250, area: 2 },
  { id: 31, name: "Bus 31", type: "generator", x: 580, y: 310, voltage: 0.99, angle: -3.8, generationMW: 600, loadMW: 0, area: 1 },
  { id: 32, name: "Bus 32", type: "generator", x: 650, y: 30, voltage: 0.99, angle: -3.5, generationMW: 650, loadMW: 0, area: 1 },
  { id: 33, name: "Bus 33", type: "generator", x: 700, y: 260, voltage: 0.995, angle: -3.0, generationMW: 632, loadMW: 0, area: 1 },
  { id: 34, name: "Bus 34", type: "generator", x: 440, y: 400, voltage: 0.99, angle: -4.1, generationMW: 508, loadMW: 0, area: 3 },
  { id: 35, name: "Bus 35", type: "generator", x: 500, y: 380, voltage: 0.99, angle: -4.0, generationMW: 500, loadMW: 0, area: 3 },
  { id: 36, name: "Bus 36", type: "generator", x: 560, y: 420, voltage: 0.99, angle: -3.9, generationMW: 500, loadMW: 0, area: 3 },
  { id: 37, name: "Bus 37", type: "generator", x: 300, y: 420, voltage: 0.99, angle: -4.3, generationMW: 540, loadMW: 0, area: 3 },
  { id: 38, name: "Bus 38", type: "generator", x: 170, y: 340, voltage: 0.99, angle: -4.4, generationMW: 500, loadMW: 0, area: 2 },
  { id: 39, name: "Bus 39", type: "generator", x: 420, y: 480, voltage: 1.03, angle: 0, generationMW: 1000, loadMW: 1104, area: 3 },
];

export const branches: Branch[] = [
  { id: 1, from: 1, to: 2, r: 0.0035, x: 0.0411, b: 0.6987, rateA: 900, loading: 0.65, status: "normal", flowMW: 585, flowDir: "forward" },
  { id: 2, from: 1, to: 39, r: 0.001, x: 0.025, b: 0.75, rateA: 2500, loading: 0.42, status: "normal", flowMW: 1050, flowDir: "forward" },
  { id: 3, from: 2, to: 3, r: 0.001, x: 0.025, b: 0.75, rateA: 1900, loading: 0.55, status: "normal", flowMW: 1045, flowDir: "forward" },
  { id: 4, from: 2, to: 25, r: 0.005, x: 0.043, b: 0.69, rateA: 900, loading: 0.48, status: "normal", flowMW: 432, flowDir: "forward" },
  { id: 5, from: 3, to: 4, r: 0.006, x: 0.048, b: 0.63, rateA: 900, loading: 0.62, status: "normal", flowMW: 558, flowDir: "forward" },
  { id: 6, from: 4, to: 5, r: 0.001, x: 0.022, b: 0.68, rateA: 1400, loading: 0.71, status: "normal", flowMW: 994, flowDir: "forward" },
  { id: 7, from: 4, to: 14, r: 0.008, x: 0.056, b: 0.58, rateA: 500, loading: 0.38, status: "normal", flowMW: 190, flowDir: "forward" },
  { id: 8, from: 5, to: 6, r: 0.002, x: 0.028, b: 0.72, rateA: 900, loading: 0.58, status: "normal", flowMW: 522, flowDir: "forward" },
  { id: 9, from: 5, to: 8, r: 0.006, x: 0.042, b: 0.65, rateA: 600, loading: 0.45, status: "normal", flowMW: 270, flowDir: "forward" },
  { id: 10, from: 6, to: 7, r: 0.005, x: 0.04, b: 0.66, rateA: 900, loading: 0.52, status: "normal", flowMW: 468, flowDir: "forward" },
  { id: 11, from: 6, to: 11, r: 0.008, x: 0.055, b: 0.61, rateA: 500, loading: 0.44, status: "normal", flowMW: 220, flowDir: "forward" },
  { id: 12, from: 6, to: 31, r: 0.002, x: 0.03, b: 0.7, rateA: 900, loading: 0.39, status: "normal", flowMW: 351, flowDir: "reverse" },
  { id: 13, from: 7, to: 8, r: 0.006, x: 0.048, b: 0.63, rateA: 700, loading: 0.56, status: "normal", flowMW: 392, flowDir: "forward" },
  { id: 14, from: 8, to: 9, r: 0.003, x: 0.035, b: 0.69, rateA: 900, loading: 0.61, status: "normal", flowMW: 549, flowDir: "forward" },
  { id: 15, from: 9, to: 39, r: 0.001, x: 0.025, b: 0.74, rateA: 1900, loading: 0.33, status: "normal", flowMW: 627, flowDir: "reverse" },
  { id: 16, from: 10, to: 11, r: 0.004, x: 0.04, b: 0.66, rateA: 500, loading: 0.42, status: "normal", flowMW: 210, flowDir: "forward" },
  { id: 17, from: 10, to: 13, r: 0.01, x: 0.065, b: 0.55, rateA: 400, loading: 0.28, status: "normal", flowMW: 112, flowDir: "forward" },
  { id: 18, from: 12, to: 11, r: 0.003, x: 0.035, b: 0.69, rateA: 500, loading: 0.52, status: "normal", flowMW: 260, flowDir: "reverse" },
  { id: 19, from: 12, to: 13, r: 0.006, x: 0.045, b: 0.64, rateA: 700, loading: 0.47, status: "normal", flowMW: 329, flowDir: "forward" },
  { id: 20, from: 13, to: 14, r: 0.006, x: 0.048, b: 0.63, rateA: 600, loading: 0.53, status: "normal", flowMW: 318, flowDir: "forward" },
  { id: 21, from: 14, to: 15, r: 0.004, x: 0.04, b: 0.66, rateA: 700, loading: 0.61, status: "normal", flowMW: 427, flowDir: "forward" },
  { id: 22, from: 15, to: 16, r: 0.01, x: 0.065, b: 0.55, rateA: 400, loading: 0.35, status: "normal", flowMW: 140, flowDir: "forward" },
  { id: 23, from: 16, to: 17, r: 0.008, x: 0.058, b: 0.59, rateA: 500, loading: 0.41, status: "normal", flowMW: 205, flowDir: "forward" },
  { id: 24, from: 16, to: 19, r: 0.01, x: 0.07, b: 0.53, rateA: 400, loading: 0.32, status: "normal", flowMW: 128, flowDir: "forward" },
  { id: 25, from: 16, to: 21, r: 0.008, x: 0.055, b: 0.6, rateA: 500, loading: 0.38, status: "normal", flowMW: 190, flowDir: "forward" },
  { id: 26, from: 16, to: 24, r: 0.012, x: 0.075, b: 0.5, rateA: 350, loading: 0.29, status: "normal", flowMW: 101, flowDir: "forward" },
  { id: 27, from: 17, to: 18, r: 0.005, x: 0.042, b: 0.65, rateA: 600, loading: 0.49, status: "normal", flowMW: 294, flowDir: "forward" },
  { id: 28, from: 17, to: 27, r: 0.006, x: 0.048, b: 0.63, rateA: 500, loading: 0.44, status: "normal", flowMW: 220, flowDir: "forward" },
  { id: 29, from: 19, to: 20, r: 0.005, x: 0.04, b: 0.66, rateA: 900, loading: 0.67, status: "normal", flowMW: 603, flowDir: "forward" },
  { id: 30, from: 19, to: 33, r: 0.002, x: 0.03, b: 0.7, rateA: 900, loading: 0.52, status: "normal", flowMW: 468, flowDir: "forward" },
  { id: 31, from: 20, to: 34, r: 0.005, x: 0.04, b: 0.66, rateA: 700, loading: 0.58, status: "normal", flowMW: 406, flowDir: "forward" },
  { id: 32, from: 21, to: 22, r: 0.004, x: 0.035, b: 0.68, rateA: 700, loading: 0.55, status: "normal", flowMW: 385, flowDir: "forward" },
  { id: 33, from: 22, to: 23, r: 0.005, x: 0.04, b: 0.66, rateA: 500, loading: 0.62, status: "normal", flowMW: 310, flowDir: "forward" },
  { id: 34, from: 23, to: 24, r: 0.003, x: 0.032, b: 0.69, rateA: 700, loading: 0.51, status: "normal", flowMW: 357, flowDir: "forward" },
  { id: 35, from: 23, to: 36, r: 0.006, x: 0.048, b: 0.63, rateA: 500, loading: 0.44, status: "normal", flowMW: 220, flowDir: "forward" },
  { id: 36, from: 24, to: 36, r: 0.008, x: 0.055, b: 0.61, rateA: 500, loading: 0.39, status: "normal", flowMW: 195, flowDir: "forward" },
  { id: 37, from: 25, to: 26, r: 0.004, x: 0.035, b: 0.68, rateA: 700, loading: 0.53, status: "normal", flowMW: 371, flowDir: "forward" },
  { id: 38, from: 25, to: 37, r: 0.006, x: 0.048, b: 0.63, rateA: 500, loading: 0.36, status: "normal", flowMW: 180, flowDir: "reverse" },
  { id: 39, from: 26, to: 27, r: 0.005, x: 0.04, b: 0.66, rateA: 600, loading: 0.49, status: "normal", flowMW: 294, flowDir: "forward" },
  { id: 40, from: 26, to: 28, r: 0.006, x: 0.045, b: 0.64, rateA: 600, loading: 0.57, status: "normal", flowMW: 342, flowDir: "forward" },
  { id: 41, from: 26, to: 29, r: 0.007, x: 0.05, b: 0.62, rateA: 500, loading: 0.51, status: "normal", flowMW: 255, flowDir: "forward" },
  { id: 42, from: 27, to: 28, r: 0.005, x: 0.04, b: 0.66, rateA: 500, loading: 0.42, status: "normal", flowMW: 210, flowDir: "forward" },
  { id: 43, from: 28, to: 29, r: 0.008, x: 0.055, b: 0.61, rateA: 400, loading: 0.38, status: "normal", flowMW: 152, flowDir: "forward" },
  { id: 44, from: 29, to: 38, r: 0.005, x: 0.04, b: 0.66, rateA: 700, loading: 0.46, status: "normal", flowMW: 322, flowDir: "forward" },
  { id: 45, from: 30, to: 38, r: 0.006, x: 0.045, b: 0.64, rateA: 500, loading: 0.41, status: "normal", flowMW: 205, flowDir: "forward" },
  { id: 46, from: 31, to: 6, r: 0.003, x: 0.03, b: 0.7, rateA: 900, loading: 0.39, status: "normal", flowMW: 351, flowDir: "forward" },
];

export const modelMetrics: ModelMetrics = {
  rocAuc: 0.9847,
  prAuc: 0.9912,
  accuracy: 0.9623,
  precision: 0.9785,
  recall: 0.9891,
  f1Score: 0.9838,
  confusionMatrix: { tp: 4392, tn: 567, fp: 118, fn: 49 },
  rocCurve: [
    { fpr: 0, tpr: 0 }, { fpr: 0.001, tpr: 0.42 }, { fpr: 0.005, tpr: 0.65 },
    { fpr: 0.01, tpr: 0.78 }, { fpr: 0.02, tpr: 0.86 }, { fpr: 0.04, tpr: 0.91 },
    { fpr: 0.06, tpr: 0.94 }, { fpr: 0.08, tpr: 0.955 }, { fpr: 0.1, tpr: 0.965 },
    { fpr: 0.15, tpr: 0.978 }, { fpr: 0.2, tpr: 0.985 }, { fpr: 0.3, tpr: 0.991 },
    { fpr: 0.4, tpr: 0.994 }, { fpr: 0.5, tpr: 0.996 }, { fpr: 0.7, tpr: 0.998 },
    { fpr: 1.0, tpr: 1.0 },
  ],
  featureImportance: [
    { feature: "Max Branch Loading", importance: 0.185 },
    { feature: "Mean Branch Loading", importance: 0.142 },
    { feature: "Std Branch Loading", importance: 0.118 },
    { feature: "Algebraic Connectivity", importance: 0.098 },
    { feature: "Max Betweenness", importance: 0.087 },
    { feature: "Generation Margin", importance: 0.076 },
    { feature: "Affected Bus Degree", importance: 0.065 },
    { feature: "Clustering Coefficient", importance: 0.054 },
    { feature: "Flow Entropy", importance: 0.048 },
    { feature: "Topological Distance", importance: 0.042 },
    { feature: "Load Concentration", importance: 0.035 },
    { feature: "Generator Admittance", importance: 0.025 },
    { feature: "Network Connectivity", importance: 0.015 },
    { feature: "Reactive Power Margin", importance: 0.008 },
    { feature: "Voltage Deviation", importance: 0.002 },
  ],
  crossValidationScores: [0.9812, 0.9834, 0.9856, 0.9878, 0.9891],
};

export const sampleCascadeSteps: CascadeStep[] = [
  {
    step: 0, timestamp: "T+0.00s", description: "Initial N-1 contingency: Branch 15 (Bus 9→Bus 39) tripped",
    trippedBranches: [15],
    loadingChanges: [
      { branchId: 14, before: 0.61, after: 0.82 },
      { branchId: 6, before: 0.71, after: 0.88 },
      { branchId: 20, before: 0.53, after: 0.74 },
      { branchId: 41, before: 0.51, after: 0.69 },
      { branchId: 44, before: 0.46, after: 0.65 },
    ],
    totalLoadLost: 0, totalGenerationLost: 0,
    islands: [],
  },
  {
    step: 1, timestamp: "T+0.15s", description: "Branch 14 (Bus 8→Bus 9) overloaded (1.05×) — tripped",
    trippedBranches: [14],
    loadingChanges: [
      { branchId: 9, before: 0.45, after: 0.91 },
      { branchId: 13, before: 0.56, after: 0.78 },
      { branchId: 16, before: 0.42, after: 0.72 },
      { branchId: 45, before: 0.41, after: 0.68 },
    ],
    totalLoadLost: 0, totalGenerationLost: 0,
    islands: [],
  },
  {
    step: 2, timestamp: "T+0.32s", description: "Branch 9 (Bus 5→Bus 8) overloaded (1.12×) — tripped",
    trippedBranches: [9],
    loadingChanges: [
      { branchId: 6, before: 0.88, after: 1.05 },
      { branchId: 8, before: 0.58, after: 0.84 },
      { branchId: 10, before: 0.52, after: 0.76 },
    ],
    totalLoadLost: 250, totalGenerationLost: 700,
    islands: [{ buses: [8, 9, 10, 11, 16], generation: 0, load: 1100 }],
  },
  {
    step: 3, timestamp: "T+0.48s", description: "Branch 6 (Bus 4→Bus 5) overloaded (1.08×) — tripped. Island formed.",
    trippedBranches: [6],
    loadingChanges: [
      { branchId: 5, before: 0.62, after: 0.95 },
      { branchId: 7, before: 0.38, after: 0.71 },
      { branchId: 46, before: 0.39, after: 0.62 },
    ],
    totalLoadLost: 650, totalGenerationLost: 1400,
    islands: [
      { buses: [8, 9, 10, 11, 16], generation: 0, load: 1100 },
      { buses: [5, 6, 7, 12, 30, 31, 38], generation: 2100, load: 1450 },
    ],
  },
  {
    step: 4, timestamp: "T+0.61s", description: "Cascading stopped. 4 branches tripped. 2 islands detected. Load shedding: 650 MW.",
    trippedBranches: [],
    loadingChanges: [],
    totalLoadLost: 650, totalGenerationLost: 1400,
    islands: [
      { buses: [8, 9, 10, 11, 16], generation: 0, load: 1100 },
      { buses: [5, 6, 7, 12, 30, 31, 38], generation: 2100, load: 1450 },
    ],
  },
];

export const sampleContingencies: ContingencyResult[] = [
  { id: "N1-15", initiatingOutage: [15], cascadeSeverity: "severe", riskScore: 0.94, unservedFraction: 0.18, branchesTripped: 4, steps: sampleCascadeSteps, totalLoadLostMW: 650, mlProbability: 0.92, mitigated: true, mitigatedUnservedFraction: 0.04 },
  { id: "N1-6", initiatingOutage: [6], cascadeSeverity: "critical", riskScore: 0.97, unservedFraction: 0.32, branchesTripped: 7, steps: [], totalLoadLostMW: 1200, mlProbability: 0.96, mitigated: true, mitigatedUnservedFraction: 0.08 },
  { id: "N1-29", initiatingOutage: [29], cascadeSeverity: "moderate", riskScore: 0.72, unservedFraction: 0.09, branchesTripped: 2, steps: [], totalLoadLostMW: 320, mlProbability: 0.71, mitigated: true, mitigatedUnservedFraction: 0.02 },
  { id: "N1-3", initiatingOutage: [3], cascadeSeverity: "none", riskScore: 0.08, unservedFraction: 0.0, branchesTripped: 0, steps: [], totalLoadLostMW: 0, mlProbability: 0.05, mitigated: false },
  { id: "N1-1", initiatingOutage: [1], cascadeSeverity: "minor", riskScore: 0.35, unservedFraction: 0.03, branchesTripped: 1, steps: [], totalLoadLostMW: 110, mlProbability: 0.31, mitigated: false },
  { id: "N1-21", initiatingOutage: [21], cascadeSeverity: "moderate", riskScore: 0.68, unservedFraction: 0.07, branchesTripped: 2, steps: [], totalLoadLostMW: 250, mlProbability: 0.65, mitigated: true, mitigatedUnservedFraction: 0.01 },
  { id: "N1-34", initiatingOutage: [34], cascadeSeverity: "none", riskScore: 0.05, unservedFraction: 0.0, branchesTripped: 0, steps: [], totalLoadLostMW: 0, mlProbability: 0.03, mitigated: false },
  { id: "N1-46", initiatingOutage: [46], cascadeSeverity: "severe", riskScore: 0.89, unservedFraction: 0.15, branchesTripped: 3, steps: [], totalLoadLostMW: 520, mlProbability: 0.87, mitigated: true, mitigatedUnservedFraction: 0.05 },
  { id: "N2-6-15", initiatingOutage: [6, 15], cascadeSeverity: "critical", riskScore: 0.99, unservedFraction: 0.45, branchesTripped: 11, steps: [], totalLoadLostMW: 2100, mlProbability: 0.98, mitigated: true, mitigatedUnservedFraction: 0.15 },
  { id: "N2-3-29", initiatingOutage: [3, 29], cascadeSeverity: "severe", riskScore: 0.91, unservedFraction: 0.21, branchesTripped: 5, steps: [], totalLoadLostMW: 780, mlProbability: 0.89, mitigated: true, mitigatedUnservedFraction: 0.06 },
];

export const sampleMitigationActions: MitigationAction[] = [
  { busId: 10, busName: "Bus 10", type: "load_shedding", powerMW: 85, costPerMW: 12.5, totalCost: 1062.5, overloadReduction: 0.12 },
  { busId: 11, busName: "Bus 11", type: "load_shedding", powerMW: 65, costPerMW: 12.5, totalCost: 812.5, overloadReduction: 0.09 },
  { busId: 8, busName: "Bus 8 (Battery)", type: "battery_discharge", powerMW: 120, costPerMW: 8.0, totalCost: 960, overloadReduction: 0.15 },
  { busId: 6, busName: "Bus 6 (Gen Ramp)", type: "generator_ramp", powerMW: 95, costPerMW: 6.5, totalCost: 617.5, overloadReduction: 0.11 },
  { busId: 31, busName: "Bus 31 (Gen Ramp)", type: "generator_ramp", powerMW: 80, costPerMW: 7.0, totalCost: 560, overloadReduction: 0.08 },
  { busId: 30, busName: "Bus 30", type: "load_shedding", powerMW: 45, costPerMW: 12.5, totalCost: 562.5, overloadReduction: 0.05 },
];