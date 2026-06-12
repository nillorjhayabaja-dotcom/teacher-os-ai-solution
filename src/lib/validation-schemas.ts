// ============================================================
// TeacherOS — Zod Validation Schemas
// ============================================================
import { z } from "zod";

// --- Auth Schemas ---
export const loginSchema = z.object({
  email: z.string().email("Valid email is required").min(1, "Email is required"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  rememberMe: z.boolean().optional().default(false),
});

export const forgotPasswordSchema = z.object({
  email: z.string().email("Valid email is required").min(1, "Email is required"),
});

export const resetPasswordSchema = z.object({
  token: z.string().min(1, "Reset token is required"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  confirmPassword: z.string().min(1, "Please confirm your password"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

export const mfaSchema = z.object({
  code: z.string().length(6, "MFA code must be 6 digits").regex(/^\d{6}$/, "Code must be numeric"),
});

// --- Student Schemas ---
export const studentSearchSchema = z.object({
  query: z.string().optional(),
  gradeLevel: z.coerce.number().min(1).max(12).optional(),
  section: z.string().optional(),
  risk: z.enum(["low", "medium", "high"]).optional(),
  status: z.enum(["active", "inactive"]).optional(),
});

export const interventionSchema = z.object({
  type: z.enum(["remediation", "counseling", "parent_meeting", "referral", "other"]),
  description: z.string().min(10, "Description must be at least 10 characters"),
  status: z.enum(["planned", "in_progress", "completed", "cancelled"]).default("planned"),
  notes: z.string().optional(),
});

// --- Gradebook Schemas ---
export const gradeEntrySchema = z.object({
  studentId: z.string().min(1),
  ww1: z.coerce.number().min(0).max(20).default(0),
  ww2: z.coerce.number().min(0).max(20).default(0),
  pt1: z.coerce.number().min(0).max(30).default(0),
  pt2: z.coerce.number().min(0).max(30).default(0),
  exam: z.coerce.number().min(0).max(50).default(0),
});

export const weightConfigSchema = z.object({
  subjectId: z.string().min(1),
  gradingPeriod: z.enum(["quarter_1", "quarter_2", "quarter_3", "quarter_4"]),
  ww: z.coerce.number().min(0).max(100),
  pt: z.coerce.number().min(0).max(100),
  qa: z.coerce.number().min(0).max(100),
}).refine((data) => data.ww + data.pt + data.qa === 100, {
  message: "Weights must sum to 100%",
  path: ["ww"],
});

// --- DLL Schemas ---
export const dllInputSchema = z.object({
  gradeLevel: z.coerce.number().min(1).max(12),
  subject: z.string().min(1, "Subject is required"),
  quarter: z.enum(["Quarter 1", "Quarter 2", "Quarter 3", "Quarter 4"]),
  melcCodes: z.array(z.string()).min(1, "Select at least one MELC"),
  weekNumber: z.coerce.number().min(1).max(40).optional(),
});

export const dllSectionSchema = z.object({
  objectives: z.string().min(10, "Objectives must be at least 10 characters"),
  content: z.string().min(10, "Content must be at least 10 characters"),
  resources: z.string().min(5, "Resources must be specified"),
  procedure: z.string().min(20, "Procedure must be at least 20 characters"),
  assessment: z.string().min(10, "Assessment must be at least 10 characters"),
  reflection: z.string().optional(),
});

// --- School Forms Schemas ---
export const formSelectionSchema = z.object({
  formType: z.enum(["SF1", "SF2", "SF5", "SF9", "SF10"]),
  schoolYear: z.string().regex(/^\d{4}-\d{4}$/, "Format: YYYY-YYYY"),
  gradeLevel: z.coerce.number().min(1).max(12),
  section: z.string().min(1),
});

// --- Communication Schemas ---
export const parentMessageSchema = z.object({
  studentId: z.string().min(1, "Student is required"),
  issue: z.enum(["absence", "grade", "behavior", "achievement"]),
  subIssue: z.string().optional(),
  channel: z.enum(["SMS", "Messenger", "Email", "Letter"]).default("SMS"),
  language: z.enum(["Tagalog", "English", "Bisaya"]).default("Tagalog"),
  tone: z.enum(["Formal", "Casual", "Urgent"]).default("Formal"),
  scheduledFor: z.string().optional(),
});

// --- Report Schemas ---
export const reportInputSchema = z.object({
  type: z.enum(["RPMS", "Monthly", "Narrative", "Accomplishment", "Compliance"]),
  title: z.string().min(5, "Title must be at least 5 characters"),
  accomplishments: z.string().min(10, "Describe key accomplishments"),
  challenges: z.string().optional(),
  interventions: z.string().optional(),
});

// --- Program Schemas ---
export const programSchema = z.object({
  name: z.string().min(3, "Program name must be at least 3 characters"),
  type: z.enum(["feeding", "drrm", "brigada", "event", "other"]),
  budget: z.coerce.number().min(0, "Budget cannot be negative"),
  startDate: z.string().min(1, "Start date is required"),
  endDate: z.string().min(1, "End date is required"),
  description: z.string().optional(),
});

// --- AI Agent Schemas ---
export const agentTaskSchema = z.object({
  agentId: z.string().min(1),
  taskInput: z.string().min(5, "Task input must be at least 5 characters"),
  context: z.record(z.unknown()).optional(),
});

// --- Workflow Schemas ---
export const workflowStepSchema = z.object({
  title: z.string().min(1),
  description: z.string().optional(),
});

// --- Settings Schemas ---
export const profileSettingsSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  email: z.string().email("Valid email is required"),
  avatar: z.string().optional(),
  gradeLevel: z.coerce.number().min(1).max(12).optional(),
  section: z.string().optional(),
});

export const notificationSettingsSchema = z.object({
  emailNotifications: z.boolean().default(true),
  smsNotifications: z.boolean().default(false),
  pushNotifications: z.boolean().default(true),
  workflowAlerts: z.boolean().default(true),
  aiSuggestions: z.boolean().default(true),
  parentReplies: z.boolean().default(true),
  marketingEmails: z.boolean().default(false),
});

// --- Type exports ---
export type LoginInput = z.infer<typeof loginSchema>;
export type GradeEntryInput = z.infer<typeof gradeEntrySchema>;
export type DLLInput = z.infer<typeof dllInputSchema>;
export type ParentMessageInput = z.infer<typeof parentMessageSchema>;
export type ReportInput = z.infer<typeof reportInputSchema>;
export type ProgramInput = z.infer<typeof programSchema>;
export type AgentTaskInput = z.infer<typeof agentTaskSchema>;