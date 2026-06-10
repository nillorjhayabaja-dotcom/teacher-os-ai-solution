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

export type GradeEntry = {
  studentId: string;
  ww1: number;
  ww2: number;
  pt1: number;
  pt2: number;
  exam: number;
  final?: number;
};

export type Program = {
  id: string;
  name: string;
  status: "planning" | "execution" | "reporting" | "completed";
  budget: number;
  spent: number;
  startDate: string;
  endDate: string;
  tasks: ProgramTask[];
};

export type ProgramTask = {
  name: string;
  startWeek: number;
  duration: number;
  status: "done" | "in-progress" | "pending";
};

export type ParentCommsLog = {
  id: string;
  studentId: string;
  date: string;
  channel: "SMS" | "Messenger" | "Letter";
  message: string;
  status: "sent" | "scheduled" | "draft";
};

export type TeachingDay = {
  date: string;
  dayName: string;
  classes: TeachingClass[];
};

export type TeachingClass = {
  id: string;
  time: string;
  subject: string;
  section: string;
  status: "upcoming" | "in-progress" | "completed";
  dllLinked?: boolean;
  attendanceCaptured?: boolean;
  reflectionDone?: boolean;
};

const firstNamesM = [
  "Juan",
  "Mark",
  "Carlo",
  "Joshua",
  "Angelo",
  "Kim",
  "Daniel",
  "Paolo",
  "Rafael",
  "Miguel",
  "Christian",
  "John Rey",
];
const firstNamesF = [
  "Maria",
  "Andrea",
  "Jasmine",
  "Bea",
  "Althea",
  "Krystel",
  "Sofia",
  "Janella",
  "Camille",
  "Erika",
  "Trisha",
  "Aira",
];
const lastNames = [
  "Dela Cruz",
  "Santos",
  "Reyes",
  "Bautista",
  "Gonzales",
  "Ramos",
  "Aquino",
  "Mendoza",
  "Castillo",
  "Cruz",
  "Villanueva",
  "Garcia",
  "Torres",
  "Flores",
  "Domingo",
];
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
    const risk: Student["risk"] =
      avg < 78 || attendance < 80 ? "high" : avg < 85 ? "medium" : "low";
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

export const mockGradeEntries: GradeEntry[] = mockStudents.map((s, i) => {
  const rng = seeded(100 + i);
  const ww1 = Math.round(10 + rng() * 10);
  const ww2 = Math.round(10 + rng() * 10);
  const pt1 = Math.round(15 + rng() * 15);
  const pt2 = Math.round(15 + rng() * 15);
  const exam = Math.round(25 + rng() * 25);
  // flag some anomalies
  const isAnomaly = i === 3; // Reyes Mario gets PT anomaly
  return {
    studentId: s.id,
    ww1: i === 7 ? 0 : ww1, // Bautista missing WW2 = 0
    ww2: ww2,
    pt1: isAnomaly ? 45 : pt1, // exceeds max 30
    pt2: pt2,
    exam: exam,
  };
});

export const mockClasses = [
  {
    id: "c1",
    time: "7:30 – 8:20",
    subject: "Mathematics 6",
    section: "Sampaguita",
    room: "Rm 201",
  },
  { id: "c2", time: "8:20 – 9:10", subject: "Science 6", section: "Rosal", room: "Rm 203" },
  { id: "c3", time: "9:30 – 10:20", subject: "English 6", section: "Ilang-Ilang", room: "Rm 205" },
  {
    id: "c4",
    time: "10:20 – 11:10",
    subject: "Araling Panlipunan 6",
    section: "Sampaguita",
    room: "Rm 201",
  },
  { id: "c5", time: "1:00 – 1:50", subject: "MAPEH 6", section: "Rosal", room: "Rm 207" },
];

export const mockMELCs = {
  Mathematics: {
    "Quarter 1": [
      {
        code: "M6NS-Ia-86",
        text: "Adds and subtracts simple fractions and mixed numbers without and with regrouping.",
      },
      {
        code: "M6NS-Ib-87",
        text: "Solves routine and non-routine problems involving addition and/or subtraction of fractions.",
      },
      { code: "M6NS-Ic-90.4", text: "Multiplies simple fractions and mixed fractions." },
    ],
    "Quarter 2": [
      {
        code: "M6NS-IIa-131",
        text: "Expresses one value as a fractional part or percentage of another.",
      },
    ],
  },
  Science: {
    "Quarter 1": [
      {
        code: "S6MT-Ia-b-1",
        text: "Describes the appearance and uses of uniform and non-uniform mixtures.",
      },
    ],
  },
  English: {
    "Quarter 1": [{ code: "EN6RC-Ia-2.15", text: "Infer the theme of literary text." }],
  },
};

export const pendingWorkflows = [
  {
    id: "w1",
    title: "DLL for Math 6 – Wednesday",
    module: "Lesson Planning",
    due: "Today",
    severity: "high" as const,
  },
  {
    id: "w2",
    title: "SF2 Attendance – Sampaguita",
    module: "Forms",
    due: "Tomorrow",
    severity: "medium" as const,
  },
  {
    id: "w3",
    title: "Quarter 1 Grades – Science 6",
    module: "Grading",
    due: "Fri",
    severity: "medium" as const,
  },
  {
    id: "w4",
    title: "Parent letter: 3 absentees",
    module: "Parent Comms",
    due: "Today",
    severity: "high" as const,
  },
  {
    id: "w5",
    title: "RPMS Monthly Report",
    module: "Reports",
    due: "Next Mon",
    severity: "low" as const,
  },
];

export const atRiskStudents = mockStudents.filter((s) => s.risk === "high").slice(0, 6);

export const performanceTrend = [
  { week: "W1", avg: 82 },
  { week: "W2", avg: 83 },
  { week: "W3", avg: 81 },
  { week: "W4", avg: 84 },
  { week: "W5", avg: 85 },
  { week: "W6", avg: 86 },
  { week: "W7", avg: 84 },
  { week: "W8", avg: 87 },
];

export const aiAgents = [
  {
    id: "lesson",
    name: "Lesson Planning Agent",
    desc: "Drafts DLLs aligned to MELC.",
    color: "bg-info/10 text-info",
    icon: "BookOpen" as const,
  },
  {
    id: "assessment",
    name: "Assessment Agent",
    desc: "Generates quizzes & rubrics.",
    color: "bg-success/10 text-success",
    icon: "ClipboardCheck" as const,
  },
  {
    id: "grade",
    name: "Grade Computation Agent",
    desc: "Computes DepEd-weighted grades.",
    color: "bg-warning/10 text-warning",
    icon: "Calculator" as const,
  },
  {
    id: "forms",
    name: "Forms Agent",
    desc: "Fills SF1–SF10 with validation.",
    color: "bg-primary/10 text-primary",
    icon: "FileText" as const,
  },
  {
    id: "report",
    name: "Report Writing Agent",
    desc: "Writes RPMS & narrative reports.",
    color: "bg-accent text-accent-foreground",
    icon: "FileSignature" as const,
  },
  {
    id: "risk",
    name: "Student Risk Analyst",
    desc: "Predicts at-risk learners.",
    color: "bg-destructive/10 text-destructive",
    icon: "AlertTriangle" as const,
  },
];

// Programs mock data
export const mockPrograms: Program[] = [
  {
    id: "p1",
    name: "Feeding Program",
    status: "execution",
    budget: 15000,
    spent: 10000,
    startDate: "2026-09-01",
    endDate: "2026-10-15",
    tasks: [
      { name: "Needs Assessment", startWeek: 1, duration: 2, status: "done" },
      { name: "Menu Planning", startWeek: 3, duration: 2, status: "done" },
      { name: "Parent Permission Slips", startWeek: 5, duration: 2, status: "in-progress" },
      { name: "Food Preparation", startWeek: 7, duration: 2, status: "pending" },
      { name: "Feeding Implementation", startWeek: 9, duration: 4, status: "pending" },
      { name: "Post-Program Report", startWeek: 13, duration: 1, status: "pending" },
    ],
  },
  {
    id: "p2",
    name: "DRRM — Earthquake Drill",
    status: "planning",
    budget: 5000,
    spent: 500,
    startDate: "2026-10-01",
    endDate: "2026-10-30",
    tasks: [
      { name: "Risk Assessment", startWeek: 1, duration: 1, status: "done" },
      { name: "Drill Planning", startWeek: 2, duration: 2, status: "in-progress" },
      { name: "Parent Notification", startWeek: 4, duration: 1, status: "pending" },
      { name: "Actual Drill", startWeek: 5, duration: 1, status: "pending" },
      { name: "Post-Drill Report", startWeek: 6, duration: 1, status: "pending" },
    ],
  },
  {
    id: "p3",
    name: "Brigada Eskwela 2026",
    status: "planning",
    budget: 20000,
    spent: 0,
    startDate: "2026-11-01",
    endDate: "2026-11-30",
    tasks: [
      { name: "Planning Committee", startWeek: 1, duration: 1, status: "pending" },
      { name: "Resource Generation", startWeek: 2, duration: 3, status: "pending" },
      { name: "Volunteer Recruitment", startWeek: 3, duration: 2, status: "pending" },
      { name: "Actual Clean-Up", startWeek: 5, duration: 1, status: "pending" },
      { name: "Accomplishment Report", startWeek: 6, duration: 1, status: "pending" },
    ],
  },
];

// Parent communication logs
export const mockParentLogs: ParentCommsLog[] = [
  {
    id: "l1",
    studentId: "s-1",
    date: "2026-09-20",
    channel: "SMS",
    message: "Reminder: Parent meeting Friday 3PM",
    status: "sent",
  },
  {
    id: "l2",
    studentId: "s-1",
    date: "2026-09-15",
    channel: "Messenger",
    message: "Grade update — Science quiz result: 85%",
    status: "sent",
  },
  {
    id: "l3",
    studentId: "s-1",
    date: "2026-09-10",
    channel: "Letter",
    message: "Regarding Juan's behavior in class",
    status: "sent",
  },
  {
    id: "l4",
    studentId: "s-3",
    date: "2026-09-22",
    channel: "SMS",
    message: "Absence notification for Mario Reyes",
    status: "sent",
  },
  {
    id: "l5",
    studentId: "s-1",
    date: "2026-09-25",
    channel: "Messenger",
    message: "Conference scheduled for Oct 1",
    status: "draft",
  },
];

// Teaching schedule (weekly)
export const mockTeachingWeek: TeachingDay[] = [
  {
    date: "2026-06-07",
    dayName: "Monday",
    classes: [
      {
        id: "m1",
        time: "7:30–8:20",
        subject: "Math 6",
        section: "Sampaguita",
        status: "completed",
        dllLinked: true,
        attendanceCaptured: true,
        reflectionDone: true,
      },
      {
        id: "m2",
        time: "8:20–9:10",
        subject: "Science 6",
        section: "Rosal",
        status: "completed",
        dllLinked: true,
        attendanceCaptured: true,
        reflectionDone: false,
      },
      {
        id: "m3",
        time: "9:30–10:20",
        subject: "English 6",
        section: "Ilang-Ilang",
        status: "completed",
        dllLinked: false,
        attendanceCaptured: true,
        reflectionDone: false,
      },
    ],
  },
  {
    date: "2026-06-08",
    dayName: "Tuesday",
    classes: [
      {
        id: "t1",
        time: "7:30–8:20",
        subject: "Math 6",
        section: "Sampaguita",
        status: "completed",
        dllLinked: true,
        attendanceCaptured: true,
        reflectionDone: true,
      },
      {
        id: "t2",
        time: "10:20–11:10",
        subject: "AP 6",
        section: "Sampaguita",
        status: "completed",
        dllLinked: false,
        attendanceCaptured: false,
        reflectionDone: false,
      },
    ],
  },
  {
    date: "2026-06-09",
    dayName: "Wednesday",
    classes: [
      {
        id: "w1",
        time: "7:30–8:20",
        subject: "Math 6",
        section: "Sampaguita",
        status: "in-progress",
        dllLinked: false,
        attendanceCaptured: false,
        reflectionDone: false,
      },
      { id: "w2", time: "8:20–9:10", subject: "Science 6", section: "Rosal", status: "upcoming" },
      { id: "w3", time: "1:00–1:50", subject: "MAPEH 6", section: "Rosal", status: "upcoming" },
    ],
  },
  {
    date: "2026-06-10",
    dayName: "Thursday",
    classes: [
      {
        id: "th1",
        time: "7:30–8:20",
        subject: "Math 6",
        section: "Sampaguita",
        status: "upcoming",
      },
      {
        id: "th2",
        time: "9:30–10:20",
        subject: "English 6",
        section: "Ilang-Ilang",
        status: "upcoming",
      },
    ],
  },
  {
    date: "2026-06-11",
    dayName: "Friday",
    classes: [
      { id: "f1", time: "7:30–8:20", subject: "Math 6", section: "Sampaguita", status: "upcoming" },
      { id: "f2", time: "10:20–11:10", subject: "AP 6", section: "Sampaguita", status: "upcoming" },
      { id: "f3", time: "1:00–1:50", subject: "MAPEH 6", section: "Rosal", status: "upcoming" },
    ],
  },
];

// Report templates
export const mockReportTemplates = [
  { id: "r1", name: "RPMS Sy 2026-2027", type: "RPMS", status: "draft", lastEdited: "Today" },
  {
    id: "r2",
    name: "Monthly Accomplishment — September",
    type: "Monthly",
    status: "in-progress",
    lastEdited: "Yesterday",
  },
  {
    id: "r3",
    name: "Narrative Report — Science Fair",
    type: "Narrative",
    status: "completed",
    lastEdited: "Sep 25",
  },
  {
    id: "r4",
    name: "Quarterly Assessment Analysis",
    type: "Narrative",
    status: "draft",
    lastEdited: "Sep 20",
  },
];
