// ============================================================
// TeacherOS — Gradebook Store (Zustand)
// ============================================================
import { create } from "zustand";
import type { GradeEntry, WeightConfig, GradeAnomaly, ApprovalStatus, GradingPeriod } from "@/types";

interface GradebookState {
  entries: GradeEntry[];
  weightConfig: WeightConfig | null;
  anomalies: GradeAnomaly[];
  selectedSubject: string;
  selectedPeriod: GradingPeriod;
  approvalStatus: ApprovalStatus;
  isComputing: boolean;
  isDirty: boolean;
}

interface GradebookActions {
  setEntries: (entries: GradeEntry[]) => void;
  updateEntry: (studentId: string, field: string, value: number) => void;
  updateBulk: (updates: Array<{ studentId: string; field: string; value: number }>) => void;
  setWeightConfig: (config: WeightConfig) => void;
  setAnomalies: (anomalies: GradeAnomaly[]) => void;
  resolveAnomaly: (anomalyId: string) => void;
  setSelectedSubject: (subject: string) => void;
  setSelectedPeriod: (period: GradingPeriod) => void;
  setApprovalStatus: (status: ApprovalStatus) => void;
  setIsComputing: (computing: boolean) => void;
  markClean: () => void;
  clear: () => void;
}

type GradebookStore = GradebookState & GradebookActions;

const initialState: GradebookState = {
  entries: [],
  weightConfig: null,
  anomalies: [],
  selectedSubject: "",
  selectedPeriod: "quarter_1",
  approvalStatus: "draft",
  isComputing: false,
  isDirty: false,
};

export const useGradebookStore = create<GradebookStore>()((set) => ({
  ...initialState,

  setEntries: (entries) => set({ entries, isDirty: false }),

  updateEntry: (studentId, field, value) =>
    set((state) => ({
      entries: state.entries.map((e) =>
        e.studentId === studentId ? { ...e, [field]: value } : e,
      ),
      isDirty: true,
    })),

  updateBulk: (updates) =>
    set((state) => ({
      entries: state.entries.map((e) => {
        const update = updates.find((u) => u.studentId === e.studentId);
        return update ? { ...e, [update.field]: update.value } : e;
      }),
      isDirty: true,
    })),

  setWeightConfig: (weightConfig) => set({ weightConfig }),
  setAnomalies: (anomalies) => set({ anomalies }),

  resolveAnomaly: (anomalyId) =>
    set((state) => ({
      anomalies: state.anomalies.map((a) =>
        a.id === anomalyId ? { ...a, status: "resolved" as const } : a,
      ),
    })),

  setSelectedSubject: (selectedSubject) => set({ selectedSubject }),
  setSelectedPeriod: (selectedPeriod) => set({ selectedPeriod }),
  setApprovalStatus: (approvalStatus) => set({ approvalStatus }),
  setIsComputing: (isComputing) => set({ isComputing }),
  markClean: () => set({ isDirty: false }),
  clear: () => set({ ...initialState }),
}));