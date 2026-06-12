// ============================================================
// TeacherOS — Student Store (Zustand)
// ============================================================
import { create } from "zustand";
import type { Student, Guardian, Intervention, RiskLevel } from "@/types";

interface StudentState {
  students: Student[];
  selectedStudent: Student | null;
  filteredIds: string[];
  searchQuery: string;
  riskFilter: RiskLevel | "all";
  sectionFilter: string | "all";
  isLoading: boolean;
}

interface StudentActions {
  setStudents: (students: Student[]) => void;
  selectStudent: (student: Student | null) => void;
  updateStudent: (id: string, updates: Partial<Student>) => void;
  addIntervention: (studentId: string, intervention: Intervention) => void;
  updateIntervention: (studentId: string, interventionId: string, updates: Partial<Intervention>) => void;
  addGuardian: (studentId: string, guardian: Guardian) => void;
  setSearchQuery: (query: string) => void;
  setRiskFilter: (risk: RiskLevel | "all") => void;
  setSectionFilter: (section: string | "all") => void;
  setLoading: (loading: boolean) => void;
  clear: () => void;
}

type StudentStore = StudentState & StudentActions;

const initialState: StudentState = {
  students: [],
  selectedStudent: null,
  filteredIds: [],
  searchQuery: "",
  riskFilter: "all",
  sectionFilter: "all",
  isLoading: false,
};

export const useStudentStore = create<StudentStore>()((set) => ({
  ...initialState,

  setStudents: (students) =>
    set({
      students,
      filteredIds: students.map((s) => s.id),
    }),

  selectStudent: (selectedStudent) => set({ selectedStudent }),

  updateStudent: (id, updates) =>
    set((state) => ({
      students: state.students.map((s) => (s.id === id ? { ...s, ...updates } : s)),
      selectedStudent:
        state.selectedStudent?.id === id
          ? { ...state.selectedStudent, ...updates }
          : state.selectedStudent,
    })),

  addIntervention: (studentId, intervention) =>
    set((state) => ({
      students: state.students.map((s) =>
        s.id === studentId
          ? { ...s, interventions: [...s.interventions, intervention] }
          : s,
      ),
      selectedStudent:
        state.selectedStudent?.id === studentId
          ? {
              ...state.selectedStudent,
              interventions: [...state.selectedStudent.interventions, intervention],
            }
          : state.selectedStudent,
    })),

  updateIntervention: (studentId, interventionId, updates) =>
    set((state) => ({
      students: state.students.map((s) =>
        s.id === studentId
          ? {
              ...s,
              interventions: s.interventions.map((i) =>
                i.id === interventionId ? { ...i, ...updates } : i,
              ),
            }
          : s,
      ),
      selectedStudent:
        state.selectedStudent?.id === studentId
          ? {
              ...state.selectedStudent,
              interventions: state.selectedStudent.interventions.map((i) =>
                i.id === interventionId ? { ...i, ...updates } : i,
              ),
            }
          : state.selectedStudent,
    })),

  addGuardian: (studentId, guardian) =>
    set((state) => ({
      students: state.students.map((s) =>
        s.id === studentId ? { ...s, guardians: [...s.guardians, guardian] } : s,
      ),
    })),

  setSearchQuery: (searchQuery) => set({ searchQuery }),
  setRiskFilter: (riskFilter) => set({ riskFilter }),
  setSectionFilter: (sectionFilter) => set({ sectionFilter }),
  setLoading: (isLoading) => set({ isLoading }),
  clear: () => set({ ...initialState }),
}));