// ============================================================
// TeacherOS — TanStack Query Hooks
// ============================================================
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/services/api";
import { useAuthStore } from "@/stores/auth-store";
import type { QueryParams } from "@/types";

// --- Query Key Factory ---
export const queryKeys = {
  auth: {
    profile: ["auth", "profile"] as const,
  },
  students: {
    all: (params?: QueryParams) => ["students", "list", params] as const,
    detail: (id: string) => ["students", "detail", id] as const,
    atRisk: (params?: QueryParams) => ["students", "at-risk", params] as const,
    interventions: (studentId: string) => ["students", "interventions", studentId] as const,
  },
  grades: {
    all: (params?: QueryParams) => ["grades", "list", params] as const,
    compute: (subjectId: string, period: string) => ["grades", "compute", subjectId, period] as const,
  },
  lessons: {
    all: (params?: QueryParams) => ["lessons", "list", params] as const,
    detail: (id: string) => ["lessons", "detail", id] as const,
    versions: (dllId: string) => ["lessons", "versions", dllId] as const,
    melcs: (subject?: string, gradeLevel?: number) => ["melcs", subject, gradeLevel] as const,
  },
  forms: {
    all: (params?: QueryParams) => ["forms", "list", params] as const,
    detail: (id: string) => ["forms", "detail", id] as const,
    validation: (id: string) => ["forms", "validation", id] as const,
  },
  messages: {
    all: (params?: QueryParams) => ["messages", "list", params] as const,
    history: (studentId: string) => ["messages", "history", studentId] as const,
  },
  reports: {
    all: (params?: QueryParams) => ["reports", "list", params] as const,
  },
  programs: {
    all: (params?: QueryParams) => ["programs", "list", params] as const,
    detail: (id: string) => ["programs", "detail", id] as const,
  },
  agents: {
    all: () => ["agents"] as const,
    runs: (agentId: string) => ["agents", "runs", agentId] as const,
  },
  notifications: {
    all: (params?: QueryParams) => ["notifications", "list", params] as const,
  },
  dashboard: {
    briefing: ["dashboard", "briefing"] as const,
    performance: (subjectId?: string) => ["dashboard", "performance", subjectId] as const,
  },
};

// ================================================================
// AUTH QUERIES
// ================================================================
export function useProfile() {
  const setUser = useAuthStore((s) => s.setUser);
  return useQuery({
    queryKey: queryKeys.auth.profile,
    queryFn: async () => {
      const user = await api.getProfile();
      setUser(user);
      return user;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function useLoginMutation() {
  const login = useAuthStore((s) => s.login);
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      api.login(email, password),
    onSuccess: (data) => {
      login(data.user, data.access_token, data.refresh_token);
    },
  });
}

export function useLogoutMutation() {
  const queryClient = useQueryClient();
  const logout = useAuthStore((s) => s.logout);
  return useMutation({
    mutationFn: () => api.logout(),
    onSuccess: () => {
      logout();
      queryClient.clear();
    },
    onError: () => {
      logout();
      queryClient.clear();
    },
  });
}

// ================================================================
// STUDENT QUERIES
// ================================================================
export function useStudents(params?: QueryParams) {
  return useQuery({
    queryKey: queryKeys.students.all(params),
    queryFn: () => api.getStudents(params),
  });
}

export function useStudent(id: string) {
  return useQuery({
    queryKey: queryKeys.students.detail(id),
    queryFn: () => api.getStudent(id),
    enabled: !!id,
  });
}

export function useAtRiskStudents(params?: QueryParams) {
  return useQuery({
    queryKey: queryKeys.students.atRisk(params),
    queryFn: () => api.getAtRiskStudents(params),
  });
}

export function useCreateStudentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof api.createStudent>[0]) => api.createStudent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
  });
}

export function useUpdateStudentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof api.updateStudent>[1] }) =>
      api.updateStudent(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
  });
}

export function useAddInterventionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ studentId, data }: { studentId: string; data: Parameters<typeof api.addIntervention>[1] }) =>
      api.addIntervention(studentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["students", "interventions"] });
    },
  });
}

// ================================================================
// GRADEBOOK QUERIES
// ================================================================
export function useGradeEntries(params?: QueryParams) {
  return useQuery({
    queryKey: queryKeys.grades.all(params),
    queryFn: () => api.getGradeEntries(params),
  });
}

export function useUpdateGradeMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof api.updateGradeEntry>[1] }) =>
      api.updateGradeEntry(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grades"] });
    },
  });
}

export function useComputeGradesMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ subjectId, gradingPeriod }: { subjectId: string; gradingPeriod: string }) =>
      api.computeGrades(subjectId, gradingPeriod),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["grades"] });
    },
  });
}

// ================================================================
// LESSON / DLL QUERIES
// ================================================================
export function useDLLs(params?: QueryParams) {
  return useQuery({
    queryKey: queryKeys.lessons.all(params),
    queryFn: () => api.getDLLs(params),
  });
}

export function useDLL(id: string) {
  return useQuery({
    queryKey: queryKeys.lessons.detail(id),
    queryFn: () => api.getDLL(id),
    enabled: !!id,
  });
}

export function useMELCs(subject?: string, gradeLevel?: number) {
  return useQuery({
    queryKey: queryKeys.lessons.melcs(subject, gradeLevel),
    queryFn: () => api.getMELCs(subject, gradeLevel),
  });
}

export function useGenerateDLLMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof api.generateDLL>[0]) => api.generateDLL(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lessons"] });
    },
  });
}

export function useUpdateDLLMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Parameters<typeof api.updateDLL>[1] }) =>
      api.updateDLL(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lessons"] });
    },
  });
}

// ================================================================
// FORM QUERIES
// ================================================================
export function useForms(params?: QueryParams) {
  return useQuery({
    queryKey: queryKeys.forms.all(params),
    queryFn: () => api.getForms(params),
  });
}

export function useForm(id: string) {
  return useQuery({
    queryKey: queryKeys.forms.detail(id),
    queryFn: () => api.getForm(id),
    enabled: !!id,
  });
}

export function useValidateFormMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.validateForm(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["forms"] });
    },
  });
}

export function useAutoFillFormMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.autoFillForm(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["forms"] });
    },
  });
}

// ================================================================
// PARENT MESSAGE QUERIES
// ================================================================
export function useMessages(params?: QueryParams) {
  return useQuery({
    queryKey: queryKeys.messages.all(params),
    queryFn: () => api.getMessages(params),
  });
}

export function useCommunicationHistory(studentId: string) {
  return useQuery({
    queryKey: queryKeys.messages.history(studentId),
    queryFn: () => api.getCommunicationHistory(studentId),
    enabled: !!studentId,
  });
}

export function useGenerateMessageMutation() {
  return useMutation({
    mutationFn: (data: Parameters<typeof api.generateMessage>[0]) => api.generateMessage(data),
  });
}

export function useSendMessageMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.sendMessage(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages"] });
    },
  });
}

// ================================================================
// REPORT QUERIES
// ================================================================
export function useReports(params?: QueryParams) {
  return useQuery({
    queryKey: queryKeys.reports.all(params),
    queryFn: () => api.getReports(params),
  });
}

export function useGenerateReportMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: Parameters<typeof api.generateReport>[0]) => api.generateReport(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
  });
}

// ================================================================
// PROGRAM QUERIES
// ================================================================
export function usePrograms(params?: QueryParams) {
  return useQuery({
    queryKey: queryKeys.programs.all(params),
    queryFn: () => api.getPrograms(params),
  });
}

export function useProgram(id: string) {
  return useQuery({
    queryKey: queryKeys.programs.detail(id),
    queryFn: () => api.getProgram(id),
    enabled: !!id,
  });
}

// ================================================================
// AGENT QUERIES
// ================================================================
export function useAgents() {
  return useQuery({
    queryKey: queryKeys.agents.all(),
    queryFn: () => api.getAgents(),
  });
}

export function useRunAgentMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ agentId, taskInput, context }: { agentId: string; taskInput: string; context?: Record<string, unknown> }) =>
      api.runAgent(agentId, taskInput, context),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] });
    },
  });
}

// ================================================================
// NOTIFICATION QUERIES
// ================================================================
export function useNotifications(params?: QueryParams) {
  return useQuery({
    queryKey: queryKeys.notifications.all(params),
    queryFn: () => api.getNotifications(params),
  });
}

export function useMarkNotificationReadMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.markNotificationRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

export function useMarkAllNotificationsReadMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => api.markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });
}

// ================================================================
// DASHBOARD QUERIES
// ================================================================
export function useDashboardBriefing() {
  return useQuery({
    queryKey: queryKeys.dashboard.briefing,
    queryFn: () => api.getDashboardBriefing(),
  });
}

export function usePerformanceTrend(subjectId?: string) {
  return useQuery({
    queryKey: queryKeys.dashboard.performance(subjectId),
    queryFn: () => api.getPerformanceTrend(subjectId),
  });
}