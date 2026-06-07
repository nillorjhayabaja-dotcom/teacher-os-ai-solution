// Realistic mock data for a Philippine elementary/HS classroom.
export type Student = {
  id: string;
  lrn: string;
  name: string;
  sex: "M" | "F";
  section: string;
  gradeLevel: number;
  attendance: number; // percent
  averageGrade: number;
  risk: "low" | "medium" | "high";
  guardian: string;
  contact: string;
};

const firstNamesM = ["Juan", "Mark", "Carlo", "Joshua", "Angelo", "Kim", "Daniel", "Paolo", "Rafael", "Miguel", "Christian", "John Rey"];
const firstNamesF = ["Maria", "Andrea", "Jasmine", "Bea", "Althea", "Krystel", "Sofia", "Janella", "Camille", "Erika", "Trisha", "Aira"];
const lastNames = ["Dela Cruz", "Santos", "Reyes", "Bautista", "Gonzales", "Ramos", "Aquino", "Mendoza", "Castillo", "Cruz", "Villanueva", "Garcia", "Torres", "Flores", "Domingo"];
const guardians = ["Mrs. Dela Cruz", "Mr. Santos", "Mrs. Reyes", "Mr. Bautista", "Mrs. Gonzales"];

function seeded(n: number) {
  return () => {
    n = (n * 9301 + 49297) % 233280;
    return n / 233280;
  };
}

export const mockStudents: Student[] = (() => {
  const rng = seeded(42);
  const sections = ["Sampaguita", "Rosal", "Ilang-Ilang"];
  return Array.from({ length: 40 }, (_, i) => {
    const sex: "M" | "F" = rng() > 0.5 ? "M" : "F";
    const first = (sex === "M" ? firstNamesM : firstNamesF)[Math.floor(rng() * 12)];
    const last = lastNames[Math.floor(rng() * lastNames.length)];
    const attendance = Math.round(70 + rng() * 30);
    const avg = Math.round(72 + rng() * 25);
    const risk: Student["risk"] = avg < 78 || attendance < 80 ? "high" : avg < 85 ? "medium" : "low";
    return {
      id: `s-${i + 1}`,
      lrn: `1370${(20000 + i).toString().padStart(8, "0")}`,
      name: `${last}, ${first}`,
      sex,
      section: sections[i % 3],
      gradeLevel: 6,
      attendance,
      averageGrade: avg,
      risk,
      guardian: guardians[i % guardians.length],
      contact: `+639${Math.floor(100000000 + rng() * 899999999)}`,
    };
  });
})();

export const mockClasses = [
  { id: "c1", time: "7:30 – 8:20", subject: "Mathematics 6", section: "Sampaguita", room: "Rm 201" },
  { id: "c2", time: "8:20 – 9:10", subject: "Science 6", section: "Rosal", room: "Rm 203" },
  { id: "c3", time: "9:30 – 10:20", subject: "English 6", section: "Ilang-Ilang", room: "Rm 205" },
  { id: "c4", time: "10:20 – 11:10", subject: "Araling Panlipunan 6", section: "Sampaguita", room: "Rm 201" },
  { id: "c5", time: "1:00 – 1:50", subject: "MAPEH 6", section: "Rosal", room: "Rm 207" },
];

export const mockMELCs = {
  Mathematics: {
    "Quarter 1": [
      { code: "M6NS-Ia-86", text: "Adds and subtracts simple fractions and mixed numbers without and with regrouping." },
      { code: "M6NS-Ib-87", text: "Solves routine and non-routine problems involving addition and/or subtraction of fractions." },
      { code: "M6NS-Ic-90.4", text: "Multiplies simple fractions and mixed fractions." },
    ],
    "Quarter 2": [
      { code: "M6NS-IIa-131", text: "Expresses one value as a fractional part or percentage of another." },
    ],
  },
  Science: {
    "Quarter 1": [
      { code: "S6MT-Ia-b-1", text: "Describes the appearance and uses of uniform and non-uniform mixtures." },
    ],
  },
  English: {
    "Quarter 1": [
      { code: "EN6RC-Ia-2.15", text: "Infer the theme of literary text." },
    ],
  },
};

export const pendingWorkflows = [
  { id: "w1", title: "DLL for Math 6 – Wednesday", module: "Lesson Planning", due: "Today", severity: "high" as const },
  { id: "w2", title: "SF2 Attendance – Sampaguita", module: "Forms", due: "Tomorrow", severity: "medium" as const },
  { id: "w3", title: "Quarter 1 Grades – Science 6", module: "Grading", due: "Fri", severity: "medium" as const },
  { id: "w4", title: "Parent letter: 3 absentees", module: "Parent Comms", due: "Today", severity: "high" as const },
  { id: "w5", title: "RPMS Monthly Report", module: "Reports", due: "Next Mon", severity: "low" as const },
];

export const atRiskStudents = mockStudents.filter((s) => s.risk === "high").slice(0, 6);

export const performanceTrend = [
  { week: "W1", avg: 82 }, { week: "W2", avg: 83 },
  { week: "W3", avg: 81 }, { week: "W4", avg: 84 },
  { week: "W5", avg: 85 }, { week: "W6", avg: 86 },
  { week: "W7", avg: 84 }, { week: "W8", avg: 87 },
];

export const aiAgents = [
  { id: "lesson", name: "Lesson Planning Agent", desc: "Drafts DLLs aligned to MELC.", color: "bg-info/10 text-info", icon: "BookOpen" },
  { id: "assessment", name: "Assessment Agent", desc: "Generates quizzes & rubrics.", color: "bg-success/10 text-success", icon: "ClipboardCheck" },
  { id: "grade", name: "Grade Computation Agent", desc: "Computes DepEd-weighted grades.", color: "bg-warning/10 text-warning", icon: "Calculator" },
  { id: "forms", name: "Forms Agent", desc: "Fills SF1–SF10 with validation.", color: "bg-primary/10 text-primary", icon: "FileText" },
  { id: "report", name: "Report Writing Agent", desc: "Writes RPMS & narrative reports.", color: "bg-accent text-accent-foreground", icon: "FileSignature" },
  { id: "risk", name: "Student Risk Analyst", desc: "Predicts at-risk learners.", color: "bg-destructive/10 text-destructive", icon: "AlertTriangle" },
] as const;
