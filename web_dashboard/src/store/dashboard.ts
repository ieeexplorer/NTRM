import { create } from "zustand";
import type { Branch, ContingencyResult, CascadeStep } from "@/lib/network-data";
import { buses, branches as initialBranches, sampleContingencies, sampleCascadeSteps, sampleMitigationActions } from "@/lib/network-data";
import type { MitigationAction } from "@/lib/network-data";

export type ActiveTab = "overview" | "network" | "cascade" | "model" | "mitigation";

interface DashboardState {
  // Navigation
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;

  // Network
  buses: typeof buses;
  branches: Branch[];
  selectedBranchId: number | null;
  setSelectedBranchId: (id: number | null) => void;

  // Cascade
  selectedContingency: ContingencyResult | null;
  cascadeSteps: CascadeStep[];
  currentCascadeStep: number;
  isCascadePlaying: boolean;
  selectContingency: (c: ContingencyResult | null) => void;
  setCurrentCascadeStep: (step: number) => void;
  setCascadePlaying: (playing: boolean) => void;
  applyCascadeStep: (step: number) => void;
  resetNetwork: () => void;

  // Mitigation
  mitigationEnabled: boolean;
  mitigationActions: MitigationAction[];
  setMitigationEnabled: (enabled: boolean) => void;

  // Controls
  showIslands: boolean;
  showFlowDirection: boolean;
  loadingThreshold: number;
  setShowIslands: (show: boolean) => void;
  setShowFlowDirection: (show: boolean) => void;
  setLoadingThreshold: (threshold: number) => void;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  activeTab: "overview",
  setActiveTab: (tab) => set({ activeTab: tab }),

  buses,
  branches: initialBranches.map(b => ({ ...b })),
  selectedBranchId: null,
  setSelectedBranchId: (id) => set({ selectedBranchId: id }),

  selectedContingency: null,
  cascadeSteps: [],
  currentCascadeStep: 0,
  isCascadePlaying: false,
  selectContingency: (c) => {
    if (c) {
      const steps = c.id === "N1-15" ? sampleCascadeSteps : generateCascadeSteps(c);
      set({
        selectedContingency: c,
        cascadeSteps: steps,
        currentCascadeStep: 0,
        isCascadePlaying: false,
      });
      get().applyCascadeStep(0);
    } else {
      set({
        selectedContingency: null,
        cascadeSteps: [],
        currentCascadeStep: 0,
        isCascadePlaying: false,
      });
      get().resetNetwork();
    }
  },
  setCurrentCascadeStep: (step) => {
    set({ currentCascadeStep: step });
    get().applyCascadeStep(step);
  },
  setCascadePlaying: (playing) => set({ isCascadePlaying: playing }),
  applyCascadeStep: (step) => {
    const { cascadeSteps } = get();
    const newBranches = initialBranches.map(b => ({ ...b }));

    // Apply all tripped branches up to this step
    for (let s = 0; s <= step; s++) {
      const cascadeStep = cascadeSteps[s];
      if (cascadeStep) {
        for (const trippedId of cascadeStep.trippedBranches) {
          const branch = newBranches.find(b => b.id === trippedId);
          if (branch) branch.status = "tripped";
        }
        for (const change of cascadeStep.loadingChanges) {
          const branch = newBranches.find(b => b.id === change.branchId);
          if (branch) {
            branch.loading = change.after;
            branch.status = change.after > 1.0 ? "overloaded" :
                            branch.status === "tripped" ? "tripped" : "normal";
            branch.flowMW = Math.round(change.after * branch.rateA);
          }
        }
      }
    }

    set({ branches: newBranches });
  },
  resetNetwork: () => set({ branches: initialBranches.map(b => ({ ...b })) }),

  mitigationEnabled: false,
  mitigationActions: sampleMitigationActions,
  setMitigationEnabled: (enabled) => set({ mitigationEnabled: enabled }),

  showIslands: true,
  showFlowDirection: true,
  loadingThreshold: 0.8,
  setShowIslands: (show) => set({ showIslands: show }),
  setShowFlowDirection: (show) => set({ showFlowDirection: show }),
  setLoadingThreshold: (threshold) => set({ loadingThreshold: threshold }),
}));

// Generate simple cascade steps for non-detailed contingencies
function generateCascadeSteps(contingency: ContingencyResult): CascadeStep[] {
  if (contingency.branchesTripped === 0) {
    return [{
      step: 0,
      timestamp: "T+0.00s",
      description: `N-1 contingency: Branch ${contingency.initiatingOutage[0]} tripped. No cascade propagation.`,
      trippedBranches: contingency.initiatingOutage,
      loadingChanges: [],
      totalLoadLost: 0,
      totalGenerationLost: 0,
      islands: [],
    }];
  }
  const steps: CascadeStep[] = [{
    step: 0,
    timestamp: "T+0.00s",
    description: `Initial contingency: Branch ${contingency.initiatingOutage.join(", ")} tripped`,
    trippedBranches: contingency.initiatingOutage,
    loadingChanges: [
      { branchId: 6, before: 0.71, after: 0.85 + Math.random() * 0.2 },
      { branchId: 14, before: 0.61, after: 0.75 + Math.random() * 0.15 },
    ],
    totalLoadLost: 0,
    totalGenerationLost: 0,
    islands: [],
  }];
  for (let i = 1; i <= contingency.branchesTripped; i++) {
    steps.push({
      step: i,
      timestamp: `T+${(i * 0.15).toFixed(2)}s`,
      description: i === contingency.branchesTripped
        ? `Cascade stopped. ${contingency.branchesTripped} branches tripped. Load shed: ${contingency.totalLoadLostMW} MW.`
        : `Branch overloaded — tripped. Propagating...`,
      trippedBranches: i < contingency.branchesTripped ? [contingency.initiatingOutage[0] + i * 3] : [],
      loadingChanges: [],
      totalLoadLost: i === contingency.branchesTripped ? contingency.totalLoadLostMW : Math.round(contingency.totalLoadLostMW * 0.3 * i / contingency.branchesTripped),
      totalGenerationLost: i === contingency.branchesTripped ? Math.round(contingency.totalLoadLostMW * 1.5) : 0,
      islands: i === contingency.branchesTripped ? [{ buses: [8, 9, 10], generation: 0, load: 500 }] : [],
    });
  }
  return steps;
}
