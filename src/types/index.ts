// ============================================================
// TeacherOS — Core Domain Types
// ============================================================

// --- Auth ---
export type UserRole = "teacher" | "master_teacher" | "head_teacher" | "principal" | "admin" | "parent" | "student";

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  avatar?: string;
  schoolId: string;
  divisionId: string;
  regionId: string;
  gradeLevel?: number;
  section?: string;
  department?: string;
  isActive: boolean;
  lastLogin?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  sessionExpiresAt?: string;
}

// --- Tenant ---
export interface Tenant {
  id: string;
  name: string;
  domain: string;
  type: "school" | "division" | "region";
  parentId?: string;
  address: string;
  logo?: string;
  config: Record<string, unknown>;
  isActive: boolean;
}

// --- Students ---
export type RiskLevel = "low" | "medium" | "high";
export type StudentSex = "M" | "F";

export interface Guardian {
  id: string;
  name: string;
  relationship: string;
  contact: string;
  email?: string;
  address?: string;
  isPrimary: boolean;
}

export interface Intervention {
  id: string;
  studentId: string;
  type: "remediation" | "counseling" | "parent_meeting" | "referral" | "other";
  description: string;
  status: "planned" | "in_progress" | "completed" | "cancelled";
  assignedBy: string;
  assignedAt: string;
  completedAt?: string;
  notes?: string;
}

export interface Student {
  id: string;
  lrn: string;
  firstName: string;
  lastName: string;
  middleName?: string;
  sex: StudentSex;
  birthDate: string;
  gradeLevel: number;
  section: string;
  schoolYear: string;
  attendance: number;
  averageGrade: number;
  risk: RiskLevel;
  guardians: Guardian[];
  interventions: Intervention[];
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// --- Gradebook ---
export type GradeComponent = "ww" | "pt" | "qa";
export type ApprovalStatus = "draft" | "review" | "final";
export type GradingPeriod = "quarter_1" | "quarter_2" | "quarter_3" | "quarter_4";

export interface GradeEntry {
  id: string;
  studentId: string;
  subjectId: string;
  gradingPeriod: GradingPeriod;
  schoolYear: string;
  ww?: Record<string, number>;
  pt?: Record<string, number>;
  qa?: number;
  final?: number;
  status: ApprovalStatus;
  overriddenBy?: string;
  overriddenAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface WeightConfig {
  subjectId: string;
  gradingPeriod: GradingPeriod;
  ww: number;
  pt: number;
  qa: number;
}

export interface GradeAnomaly {
  id: string;
  studentId: string;
  field: string;
  issue: string;
  severity: "error" | "warning";
  suggestion: string;
  status: "open" | "resolved" | "ignored";
}

// --- Lessons ---
export interface MELC {
  code: string;
  text: string;
  gradeLevel: number;
  subject: string;
  quarter: string;
}

export interface DLL {
  id: string;
  subjectId: string;
  gradeLevel: number;
  section: string;
  quarter: string;
  weekNumber: number;
  melcCodes: string[];
  objectives: string;
  content: string;
  resources: string;
  procedure: string;
  assessment: string;
  reflection: string;
  status: "draft" | "review" | "approved" | "archived";
  version: number;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface DLLVersion {
  id: string;
  dllId: string;
  version: number;
  snapshot: Partial<DLL>;
  createdBy: string;
  createdAt: string;
  notes?: string;
}

// --- School Forms ---
export type FormType = "SF1" | "SF2" | "SF5" | "SF9" | "SF10";

export interface SchoolForm {
  id: string;
  type: FormType;
  schoolYear: string;
  gradeLevel: number;
  section: string;
  month?: string;
  quarter?: string;
  status: "draft" | "validated" | "submitted" | "approved";
  validationErrors: FormValidationError[];
  data: Record<string, unknown>;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface FormValidationError {
  field: string;
  studentId?: string;
  message: string;
  severity: "error" | "warning";
  suggestion?: string;
}

// --- Communication ---
export type CommunicationChannel = "SMS" | "Messenger" | "Email" | "Letter" | "Home_Visit";
export type MessageStatus = "draft" | "sent" | "delivered" | "read" | "failed";
export type MessageLanguage = "Tagalog" | "English" | "Bisaya";
export type MessageTone = "Formal" | "Casual" | "Urgent";

export interface ParentMessage {
  id: string;
  studentId: string;
  recipientName: string;
  recipientContact: string;
  channel: CommunicationChannel;
  subject: string;
  body: string;
  language: MessageLanguage;
  tone: MessageTone;
  status: MessageStatus;
  scheduledFor?: string;
  sentAt?: string;
  readAt?: string;
  createdBy: string;
  createdAt: string;
}

export interface HomeVisitRecord {
  id: string;
  studentId: string;
  date: string;
  purpose: string;
  findings: string;
  recommendations: string;
  conductedBy: string;
  nextVisit?: string;
}

export interface MeetingLog {
  id: string;
  studentId: string;
  date: string;
  type: "parent_teacher" | "conference" | "hearing";
  attendees: string[];
  minutes: string;
  actionItems: string[];
  status: "scheduled" | "completed" | "cancelled";
}

// --- Reports ---
export type ReportType = "RPMS" | "Monthly" | "Narrative" | "Accomplishment" | "Compliance";

export interface Report {
  id: string;
  type: ReportType;
  title: string;
  content: string;
  status: "draft" | "review" | "completed" | "submitted";
  version: number;
  evidence: string[];
  createdBy: string;
  approvedBy?: string;
  createdAt: string;
  updatedAt: string;
}

// --- Programs ---
export type ProgramStatus = "planning" | "execution" | "reporting" | "completed";
export type TaskStatus = "pending" | "in_progress" | "done";

export interface ProgramTask {
  id: string;
  programId: string;
  name: string;
  description?: string;
  startWeek: number;
  duration: number;
  status: TaskStatus;
  assignedTo?: string;
}

export interface Program {
  id: string;
  name: string;
  type: "feeding" | "drrm" | "brigada" | "event" | "other";
  status: ProgramStatus;
  budget: number;
  spent: number;
  startDate: string;
  endDate: string;
  tasks: ProgramTask[];
  description?: string;
  createdBy: string;
  createdAt: string;
}

// --- AI Agents ---
export type AgentType = "lesson" | "assessment" | "grade" | "forms" | "report" | "risk";

export interface AIAgent {
  id: string;
  type: AgentType;
  name: string;
  description: string;
  status: "idle" | "running" | "completed" | "error";
  config: Record<string, unknown>;
  lastRun?: AgentRun;
}

export interface AgentRun {
  id: string;
  agentId: string;
  taskInput: string;
  status: "running" | "completed" | "failed";
  startedAt: string;
  completedAt?: string;
  output?: string;
  logs: string[];
  tokenUsage?: number;
  error?: string;
}

// --- Workflow ---
export interface WorkflowStep {
  id: number;
  title: string;
  description?: string;
  status: "pending" | "active" | "completed" | "error";
}

export interface Workflow {
  id: string;
  type: string;
  title: string;
  steps: WorkflowStep[];
  currentStep: number;
  status: "not_started" | "in_progress" | "completed" | "cancelled";
  context: Record<string, unknown>;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

// --- Notifications ---
export type NotificationType = "workflow" | "ai" | "alert" | "reminder" | "system";

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  link?: string;
  createdAt: string;
}

// --- Dashboard ---
export interface DailyBriefing {
  date: string;
  summary: string;
  pendingWorkflows: number;
  atRiskCount: number;
  classesToday: number;
  aiSuggestions: string[];
}

export interface PerformanceTrend {
  week: string;
  avg: number;
  subject?: string;
}

// --- Common ---
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, string[]>;
}

export interface QueryParams {
  page?: number;
  pageSize?: number;
  search?: string;
  sort?: string;
  order?: "asc" | "desc";
  filters?: Record<string, string | number | boolean>;
}