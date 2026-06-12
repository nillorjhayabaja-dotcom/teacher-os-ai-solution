// ============================================================
// TeacherOS — Lesson Planning Store (Zustand)
// ============================================================
import { create } from "zustand";
import type { DLL, MELC, DLLVersion } from "@/types";

interface LessonState {
  currentDLL: DLL | null;
  savedDLLs: DLL[];
  versions: DLLVersion[];
  selectedMELCs: MELC[];
  selectedSubject: string;
  selectedGrade: number;
  selectedQuarter: string;
  isGenerating: boolean;
  isAutosaving: boolean;
}

interface LessonActions {
  setCurrentDLL: (dll: DLL | null) => void;
  updateDLL: (updates: Partial<DLL>) => void;
  setSavedDLLs: (dlls: DLL[]) => void;
  addVersion: (version: DLLVersion) => void;
  setVersions: (versions: DLLVersion[]) => void;
  toggleMELC: (melc: MELC) => void;
  clearMELCs: () => void;
  setSelectedSubject: (subject: string) => void;
  setSelectedGrade: (grade: number) => void;
  setSelectedQuarter: (quarter: string) => void;
  setIsGenerating: (generating: boolean) => void;
  setIsAutosaving: (autosaving: boolean) => void;
  clear: () => void;
}

type LessonStore = LessonState & LessonActions;

const initialState: LessonState = {
  currentDLL: null,
  savedDLLs: [],
  versions: [],
  selectedMELCs: [],
  selectedSubject: "Mathematics",
  selectedGrade: 6,
  selectedQuarter: "Quarter 1",
  isGenerating: false,
  isAutosaving: false,
};

export const useLessonStore = create<LessonStore>()((set) => ({
  ...initialState,

  setCurrentDLL: (currentDLL) => set({ currentDLL }),

  updateDLL: (updates) =>
    set((state) => ({
      currentDLL: state.currentDLL ? { ...state.currentDLL, ...updates } : null,
    })),

  setSavedDLLs: (savedDLLs) => set({ savedDLLs }),

  addVersion: (version) =>
    set((state) => ({
      versions: [version, ...state.versions],
    })),

  setVersions: (versions) => set({ versions }),

  toggleMELC: (melc) =>
    set((state) => {
      const exists = state.selectedMELCs.some((m) => m.code === melc.code);
      return {
        selectedMELCs: exists
          ? state.selectedMELCs.filter((m) => m.code !== melc.code)
          : [...state.selectedMELCs, melc],
      };
    }),

  clearMELCs: () => set({ selectedMELCs: [] }),

  setSelectedSubject: (selectedSubject) => set({ selectedSubject }),
  setSelectedGrade: (selectedGrade) => set({ selectedGrade }),
  setSelectedQuarter: (selectedQuarter) => set({ selectedQuarter }),
  setIsGenerating: (isGenerating) => set({ isGenerating }),
  setIsAutosaving: (isAutosaving) => set({ isAutosaving }),
  clear: () => set({ ...initialState }),
}));