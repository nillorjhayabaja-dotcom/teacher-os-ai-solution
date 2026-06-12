// ============================================================
// TeacherOS — Workflow Store (Zustand)
// ============================================================
import { create } from "zustand";
import type { Workflow, WorkflowStep } from "@/types";

interface WorkflowState {
  activeWorkflows: Workflow[];
  currentWorkflow: Workflow | null;
  workflowHistory: Workflow[];
  isLoading: boolean;
}

interface WorkflowActions {
  setActiveWorkflows: (workflows: Workflow[]) => void;
  setCurrentWorkflow: (workflow: Workflow | null) => void;
  updateWorkflowStep: (workflowId: string, stepId: number, updates: Partial<WorkflowStep>) => void;
  advanceStep: (workflowId: string) => void;
  completeWorkflow: (workflowId: string) => void;
  cancelWorkflow: (workflowId: string) => void;
  addToHistory: (workflow: Workflow) => void;
  setLoading: (loading: boolean) => void;
  clear: () => void;
}

type WorkflowStore = WorkflowState & WorkflowActions;

const initialState: WorkflowState = {
  activeWorkflows: [],
  currentWorkflow: null,
  workflowHistory: [],
  isLoading: false,
};

export const useWorkflowStore = create<WorkflowStore>()((set, get) => ({
  ...initialState,

  setActiveWorkflows: (activeWorkflows) => set({ activeWorkflows }),

  setCurrentWorkflow: (currentWorkflow) => set({ currentWorkflow }),

  updateWorkflowStep: (workflowId, stepId, updates) =>
    set((state) => ({
      activeWorkflows: state.activeWorkflows.map((w) =>
        w.id === workflowId
          ? {
              ...w,
              steps: w.steps.map((s) =>
                s.id === stepId ? { ...s, ...updates } : s,
              ),
            }
          : w,
      ),
      currentWorkflow:
        state.currentWorkflow?.id === workflowId
          ? {
              ...state.currentWorkflow,
              steps: state.currentWorkflow.steps.map((s) =>
                s.id === stepId ? { ...s, ...updates } : s,
              ),
            }
          : state.currentWorkflow,
    })),

  advanceStep: (workflowId) =>
    set((state) => {
      const updateWorkflow = (w: Workflow) => {
        if (w.currentStep >= w.steps.length) return w;
        const newSteps = w.steps.map((s) =>
          s.id === w.currentStep ? { ...s, status: "completed" as const } : s,
        );
        return {
          ...w,
          currentStep: w.currentStep + 1,
          steps: newSteps,
          status: w.currentStep + 1 > w.steps.length ? ("completed" as const) : w.status,
        };
      };

      return {
        activeWorkflows: state.activeWorkflows.map((w) =>
          w.id === workflowId ? updateWorkflow(w) : w,
        ),
        currentWorkflow:
          state.currentWorkflow?.id === workflowId
            ? updateWorkflow(state.currentWorkflow)
            : state.currentWorkflow,
      };
    }),

  completeWorkflow: (workflowId) =>
    set((state) => ({
      activeWorkflows: state.activeWorkflows.map((w) =>
        w.id === workflowId
          ? { ...w, status: "completed" as const, steps: w.steps.map((s) => ({ ...s, status: "completed" as const })) }
          : w,
      ),
      currentWorkflow:
        state.currentWorkflow?.id === workflowId
          ? { ...state.currentWorkflow, status: "completed" as const }
          : state.currentWorkflow,
    })),

  cancelWorkflow: (workflowId) =>
    set((state) => ({
      activeWorkflows: state.activeWorkflows.map((w) =>
        w.id === workflowId ? { ...w, status: "cancelled" as const } : w,
      ),
    })),

  addToHistory: (workflow) =>
    set((state) => ({
      workflowHistory: [workflow, ...state.workflowHistory].slice(0, 50),
    })),

  setLoading: (isLoading) => set({ isLoading }),
  clear: () => set({ ...initialState }),
}));