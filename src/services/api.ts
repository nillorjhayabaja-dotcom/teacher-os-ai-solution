// ============================================================
// TeacherOS — API Client
// ============================================================
import { useAuthStore } from "@/stores/auth-store";
import type { ApiError, PaginatedResponse, QueryParams } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

type RequestOptions = {
  method?: string;
  body?: unknown;
  params?: QueryParams;
  headers?: Record<string, string>;
  signal?: AbortSignal;
};

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getAuthHeaders(): Record<string, string> {
    const token = useAuthStore.getState().accessToken;
    if (!token) return {};
    return { Authorization: `Bearer ${token}` };
  }

  private buildUrl(path: string, params?: QueryParams): string {
    const url = new URL(`${this.baseUrl}${path}`, window.location.origin);
    if (params) {
      if (params.page) url.searchParams.set("page", params.page.toString());
      if (params.pageSize) url.searchParams.set("page_size", params.pageSize.toString());
      if (params.search) url.searchParams.set("search", params.search);
      if (params.sort) url.searchParams.set("sort", params.sort);
      if (params.order) url.searchParams.set("order", params.order);
      if (params.filters) {
        Object.entries(params.filters).forEach(([key, value]) => {
          url.searchParams.set(key, String(value));
        });
      }
    }
    return url.toString();
  }

  private async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { method = "GET", body, params, headers: extraHeaders, signal } = options;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...this.getAuthHeaders(),
      ...extraHeaders,
    };

    const config: RequestInit = {
      method,
      headers,
      signal,
    };

    if (body && method !== "GET") {
      config.body = JSON.stringify(body);
    }

    const url = this.buildUrl(path, params);

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        const apiError: ApiError = {
          code: errorBody.code || "UNKNOWN_ERROR",
          message: errorBody.message || `HTTP ${response.status}: ${response.statusText}`,
          details: errorBody.details,
        };

        if (response.status === 401) {
          useAuthStore.getState().logout();
        }

        throw apiError;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message === "Failed to fetch") {
        throw {
          code: "NETWORK_ERROR",
          message: "Unable to connect to the server. Please check your connection.",
        } as ApiError;
      }
      throw error;
    }
  }

  // --- Auth ---
  login = (email: string, password: string) =>
    this.request<{ user: import("@/types").User; access_token: string; refresh_token: string }>(
      "/auth/login",
      { method: "POST", body: { email, password } },
    );

  logout = () => this.request<void>("/auth/logout", { method: "POST" });

  refreshToken = (refreshToken: string) =>
    this.request<{ access_token: string; refresh_token: string }>("/auth/refresh", {
      method: "POST",
      body: { refresh_token: refreshToken },
    });

  forgotPassword = (email: string) =>
    this.request<void>("/auth/forgot-password", { method: "POST", body: { email } });

  resetPassword = (token: string, password: string) =>
    this.request<void>("/auth/reset-password", { method: "POST", body: { token, password } });

  verifyMfa = (code: string) =>
    this.request<{ access_token: string; refresh_token: string }>("/auth/mfa/verify", {
      method: "POST",
      body: { code },
    });

  getProfile = () => this.request<import("@/types").User>("/auth/profile");

  updateProfile = (data: Partial<import("@/types").User>) =>
    this.request<import("@/types").User>("/auth/profile", { method: "PATCH", body: data });

  // --- Students ---
  getStudents = (params?: QueryParams) =>
    this.request<PaginatedResponse<import("@/types").Student>>("/students", { params });

  getStudent = (id: string) =>
    this.request<import("@/types").Student>(`/students/${id}`);

  createStudent = (data: Partial<import("@/types").Student>) =>
    this.request<import("@/types").Student>("/students", { method: "POST", body: data });

  updateStudent = (id: string, data: Partial<import("@/types").Student>) =>
    this.request<import("@/types").Student>(`/students/${id}`, { method: "PATCH", body: data });

  addIntervention = (studentId: string, data: Partial<import("@/types").Intervention>) =>
    this.request<import("@/types").Intervention>(`/students/${studentId}/interventions`, {
      method: "POST",
      body: data,
    });

  getAtRiskStudents = (params?: QueryParams) =>
    this.request<import("@/types").Student[]>("/students/at-risk", { params });

  // --- Grades ---
  getGradeEntries = (params?: QueryParams) =>
    this.request<PaginatedResponse<import("@/types").GradeEntry>>("/grades", { params });

  updateGradeEntry = (id: string, data: Partial<import("@/types").GradeEntry>) =>
    this.request<import("@/types").GradeEntry>(`/grades/${id}`, { method: "PATCH", body: data });

  bulkUpdateGrades = (updates: Array<{ id: string; data: Partial<import("@/types").GradeEntry> }>) =>
    this.request<{ updated: number }>("/grades/bulk", { method: "POST", body: { updates } });

  computeGrades = (subjectId: string, gradingPeriod: string) =>
    this.request<{ entries: import("@/types").GradeEntry[]; anomalies: import("@/types").GradeAnomaly[] }>(
      "/grades/compute",
      { method: "POST", body: { subject_id: subjectId, grading_period: gradingPeriod } },
    );

  finalizeGrades = (subjectId: string, gradingPeriod: string) =>
    this.request<void>("/grades/finalize", { method: "POST", body: { subject_id: subjectId, grading_period: gradingPeriod } });

  // --- DLL / Lessons ---
  getDLLs = (params?: QueryParams) =>
    this.request<PaginatedResponse<import("@/types").DLL>>("/lessons", { params });

  getDLL = (id: string) =>
    this.request<import("@/types").DLL>(`/lessons/${id}`);

  createDLL = (data: Partial<import("@/types").DLL>) =>
    this.request<import("@/types").DLL>("/lessons", { method: "POST", body: data });

  updateDLL = (id: string, data: Partial<import("@/types").DLL>) =>
    this.request<import("@/types").DLL>(`/lessons/${id}`, { method: "PATCH", body: data });

  generateDLL = (data: { gradeLevel: number; subject: string; quarter: string; melcCodes: string[] }) =>
    this.request<import("@/types").DLL>("/lessons/generate", { method: "POST", body: data });

  getMELCs = (subject?: string, gradeLevel?: number) =>
    this.request<import("@/types").MELC[]>("/melcs", { params: { filters: { subject: subject || "", gradeLevel: gradeLevel || 0 } } });

  getDLLVersions = (dllId: string) =>
    this.request<import("@/types").DLLVersion[]>(`/lessons/${dllId}/versions`);

  // --- School Forms ---
  getForms = (params?: QueryParams) =>
    this.request<PaginatedResponse<import("@/types").SchoolForm>>("/forms", { params });

  getForm = (id: string) =>
    this.request<import("@/types").SchoolForm>(`/forms/${id}`);

  createForm = (data: Partial<import("@/types").SchoolForm>) =>
    this.request<import("@/types").SchoolForm>("/forms", { method: "POST", body: data });

  validateForm = (id: string) =>
    this.request<{ errors: import("@/types").FormValidationError[] }>(`/forms/${id}/validate`, {
      method: "POST",
    });

  autoFillForm = (id: string) =>
    this.request<import("@/types").SchoolForm>(`/forms/${id}/autofill`, { method: "POST" });

  submitForm = (id: string) =>
    this.request<import("@/types").SchoolForm>(`/forms/${id}/submit`, { method: "POST" });

  exportForm = (id: string, format: "pdf" | "excel") =>
    this.request<Blob>(`/forms/${id}/export`, {
      method: "GET",
      headers: { Accept: format === "pdf" ? "application/pdf" : "application/vnd.ms-excel" },
    });

  // --- Parent Communication ---
  getMessages = (params?: QueryParams) =>
    this.request<PaginatedResponse<import("@/types").ParentMessage>>("/messages", { params });

  createMessage = (data: Partial<import("@/types").ParentMessage>) =>
    this.request<import("@/types").ParentMessage>("/messages", { method: "POST", body: data });

  sendMessage = (id: string) =>
    this.request<import("@/types").ParentMessage>(`/messages/${id}/send`, { method: "POST" });

  generateMessage = (data: { studentId: string; issue: string; language: string; tone: string }) =>
    this.request<{ body: string }>("/messages/generate", { method: "POST", body: data });

  getCommunicationHistory = (studentId: string) =>
    this.request<import("@/types").ParentMessage[]>(`/students/${studentId}/messages`);

  // --- Reports ---
  getReports = (params?: QueryParams) =>
    this.request<PaginatedResponse<import("@/types").Report>>("/reports", { params });

  createReport = (data: Partial<import("@/types").Report>) =>
    this.request<import("@/types").Report>("/reports", { method: "POST", body: data });

  generateReport = (data: { type: string; title: string; accomplishments: string; challenges?: string; interventions?: string }) =>
    this.request<import("@/types").Report>("/reports/generate", { method: "POST", body: data });

  attachEvidence = (reportId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return this.request<{ url: string }>(`/reports/${reportId}/evidence`, {
      method: "POST",
      headers: { "Content-Type": "multipart/form-data" },
      body: formData,
    });
  };

  submitReport = (id: string) =>
    this.request<import("@/types").Report>(`/reports/${id}/submit`, { method: "POST" });

  // --- Programs ---
  getPrograms = (params?: QueryParams) =>
    this.request<PaginatedResponse<import("@/types").Program>>("/programs", { params });

  getProgram = (id: string) =>
    this.request<import("@/types").Program>(`/programs/${id}`);

  createProgram = (data: Partial<import("@/types").Program>) =>
    this.request<import("@/types").Program>("/programs", { method: "POST", body: data });

  updateProgram = (id: string, data: Partial<import("@/types").Program>) =>
    this.request<import("@/types").Program>(`/programs/${id}`, { method: "PATCH", body: data });

  addTask = (programId: string, data: Partial<import("@/types").ProgramTask>) =>
    this.request<import("@/types").ProgramTask>(`/programs/${programId}/tasks`, {
      method: "POST",
      body: data,
    });

  // --- AI Agents ---
  getAgents = () => this.request<import("@/types").AIAgent[]>("/agents");

  runAgent = (agentId: string, taskInput: string, context?: Record<string, unknown>) =>
    this.request<import("@/types").AgentRun>(`/agents/${agentId}/run`, {
      method: "POST",
      body: { task_input: taskInput, context },
    });

  getAgentRuns = (agentId: string) =>
    this.request<import("@/types").AgentRun[]>(`/agents/${agentId}/runs`);

  // --- Notifications ---
  getNotifications = (params?: QueryParams) =>
    this.request<PaginatedResponse<import("@/types").Notification>>("/notifications", { params });

  markNotificationRead = (id: string) =>
    this.request<void>(`/notifications/${id}/read`, { method: "POST" });

  markAllNotificationsRead = () =>
    this.request<void>("/notifications/read-all", { method: "POST" });

  // --- Dashboard ---
  getDashboardBriefing = () =>
    this.request<import("@/types").DailyBriefing>("/dashboard/briefing");

  getPerformanceTrend = (subjectId?: string) =>
    this.request<import("@/types").PerformanceTrend[]>("/dashboard/performance", {
      params: { filters: subjectId ? { subject_id: subjectId } : undefined },
    });

  // --- Uploads ---
  uploadFile = (file: File, folder?: string) => {
    const formData = new FormData();
    formData.append("file", file);
    if (folder) formData.append("folder", folder);
    return this.request<{ url: string; filename: string; size: number }>("/upload", {
      method: "POST",
      body: formData,
    });
  };

  // --- WebSocket URL ---
  getWebSocketUrl = (): string => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}/ws`;
  };
}

export const api = new ApiClient(API_BASE_URL);