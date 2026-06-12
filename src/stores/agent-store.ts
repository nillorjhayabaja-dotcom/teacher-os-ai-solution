// ============================================================
// TeacherOS — AI Agent Store (Zustand)
// ============================================================
import { create } from "zustand";
import type { AIAgent, AgentRun, AgentType } from "@/types";

interface AgentState {
  agents: AIAgent[];
  selectedAgent: AIAgent | null;
  currentRun: AgentRun | null;
  runHistory: AgentRun[];
  isRunning: boolean;
}

interface AgentActions {
  setAgents: (agents: AIAgent[]) => void;
  selectAgent: (agent: AIAgent | null) => void;
  updateAgentStatus: (agentId: string, status: AIAgent["status"]) => void;
  setCurrentRun: (run: AgentRun | null) => void;
  addRunLog: (log: string) => void;
  completeRun: (output: string, tokenUsage?: number) => void;
  failRun: (error: string) => void;
  addToHistory: (run: AgentRun) => void;
  clearCurrentRun: () => void;
}

type AgentStore = AgentState & AgentActions;

const initialState: AgentState = {
  agents: [],
  selectedAgent: null,
  currentRun: null,
  runHistory: [],
  isRunning: false,
};

export const useAgentStore = create<AgentStore>()((set, get) => ({
  ...initialState,

  setAgents: (agents) => set({ agents }),

  selectAgent: (selectedAgent) => set({ selectedAgent }),

  updateAgentStatus: (agentId, status) =>
    set((state) => ({
      agents: state.agents.map((a) => (a.id === agentId ? { ...a, status } : a)),
    })),

  setCurrentRun: (currentRun) =>
    set({ currentRun, isRunning: currentRun?.status === "running" }),

  addRunLog: (log) =>
    set((state) => ({
      currentRun: state.currentRun
        ? { ...state.currentRun, logs: [...state.currentRun.logs, log] }
        : null,
    })),

  completeRun: (output, tokenUsage) =>
    set((state) => ({
      currentRun: state.currentRun
        ? {
            ...state.currentRun,
            status: "completed" as const,
            output,
            tokenUsage: tokenUsage || state.currentRun.tokenUsage,
            completedAt: new Date().toISOString(),
          }
        : null,
      isRunning: false,
    })),

  failRun: (error) =>
    set((state) => ({
      currentRun: state.currentRun
        ? {
            ...state.currentRun,
            status: "failed" as const,
            error,
            completedAt: new Date().toISOString(),
          }
        : null,
      isRunning: false,
    })),

  addToHistory: (run) =>
    set((state) => ({
      runHistory: [run, ...state.runHistory].slice(0, 25),
    })),

  clearCurrentRun: () => set({ currentRun: null, isRunning: false }),
}));