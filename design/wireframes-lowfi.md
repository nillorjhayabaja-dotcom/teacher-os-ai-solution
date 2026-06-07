# TeacherOS — Low-Fidelity Wireframes

## Conventions Used

```
[ Header Bar ]
[ Sidebar ] [ Content Area ]
[ Panel ]
[ Table: Col1 | Col2 | Col3 ]
[ Button ]
============ <separator>
┌──────────┐ <card/box>
│  Label   │
│  Value   │
└──────────┘
(...) <collapsible>
```

---

## 1. Login Screen

```
┌─────────────────────────────────────────────────────────────────────┐
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │              [🧠] TeacherOS Philippines                      │  │
│  │         AI Operating System for Teachers                     │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────────────┐                    │  │
│  │  │  DepEd Email or LRN                  │                    │  │
│  │  └─────────────────────────────────────┘                    │  │
│  │  ┌─────────────────────────────────────┐                    │  │
│  │  │  Password                            │                    │  │
│  │  └─────────────────────────────────────┘                    │  │
│  │                                                              │  │
│  │  [ ✓ Remember me ]              [ Forgot password? ]        │  │
│  │                                                              │  │
│  │  ┌─────────────────────────────┐                            │  │
│  │  │       Sign In               │                            │  │
│  │  └─────────────────────────────┘                            │  │
│  │                                                              │  │
│  │  ─── or sign in with ───                                     │  │
│  │                                                              │  │
│  │  [ Google ]  [ Microsoft ]  [ DepEd SSO ]                    │  │
│  │                                                              │  │
│  │  Don't have an account? [ Sign up free ]                     │  │
│  │                                                              │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Onboarding Wizard — Step 1: Role & Grade Selection

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Back]                    Setup Wizard                    [Skip]  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Step 1 of 4: Tell us about you                               │  │
│  │  ●●●○○○○                                                     │  │
│  │                                                               │  │
│  │  What is your role?                                            │  │
│  │                                                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                   │  │
│  │  │  [👤]             │  │  [👥]             │                   │  │
│  │  │  Subject Teacher │  │  Class Adviser   │                   │  │
│  │  │  Teaches multiple│  │  Manages 1 class │                   │  │
│  │  └──────────────────┘  └──────────────────┘                   │  │
│  │                                                               │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                   │  │
│  │  │  [📋]             │  │  [🏫]             │                   │  │
│  │  │  Coordinator     │  │  Master Teacher  │                   │  │
│  │  │  Program lead    │  │  Mentor/Coach    │                   │  │
│  │  └──────────────────┘  └──────────────────┘                   │  │
│  │                                                               │  │
│  │  Grade Level(s) you handle:                                   │  │
│  │  [1] [2] [3] [4] [5] [6] [7] [8] [9] [10] [11] [12]         │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────┐                           │  │
│  │  │         Continue               │                           │  │
│  │  └────────────────────────────────┘                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Onboarding Wizard — Step 2: Subject Assignment

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Back]                    Setup Wizard                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Step 2 of 4: Your Subjects                                  │  │
│  │  ●●○○○○○                                                    │  │
│  │                                                               │  │
│  │  Select the subjects you teach:                                │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────────────────────────────┐   │  │
│  │  │  [?] Search subjects...                                │   │  │
│  │  └────────────────────────────────────────────────────────┘   │  │
│  │                                                               │  │
│  │  [✓] Mathematics                                              │  │
│  │  [✓] Science                                                  │  │
│  │  [ ] English                                                   │  │
│  │  [✓] Filipino                                                  │  │
│  │  [ ] Araling Panlipunan                                        │  │
│  │  [✓] MAPEH                                                     │  │
│  │  [ ] Edukasyon sa Pagpapakatao                                 │  │
│  │  [ ] TLE / EPP                                                 │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────┐                           │  │
│  │  │         Continue               │                           │  │
│  │  └────────────────────────────────┘                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Onboarding Wizard — Step 3: Class Setup

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Back]                    Setup Wizard                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Step 3 of 4: Set up your classes                            │  │
│  │  ●●●○○○○                                                    │  │
│  │                                                               │  │
│  │  ┌──────────────────────────────────────────────────────────┐ │  │
│  │  │  Section Name     │  Subject    │  No. of Students  [X] │ │  │
│  │  ├──────────────────────────────────────────────────────────┤ │  │
│  │  │  Sampaguita       │  Math 6     │  40                  │ │  │
│  │  │  Rosal            │  Science 6  │  38                  │ │  │
│  │  │  Ilang-Ilang      │  English 6  │  42                  │ │  │
│  │  └──────────────────────────────────────────────────────────┘ │  │
│  │                                                               │  │
│  │  [ + Add another section ]                                     │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────┐                           │  │
│  │  │         Continue               │                           │  │
│  │  └────────────────────────────────┘                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Onboarding Wizard — Step 4: Quick Start

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Back]                    Setup Wizard                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Step 4 of 4: You're all set!                                 │  │
│  │  ●●●●○                                                       │  │
│  │                                                               │  │
│  │  [🎉] Your TeacherOS workspace is ready!                      │  │
│  │                                                               │  │
│  │  Here's what you can do next:                                  │  │
│  │                                                               │  │
│  │  1. 📘 Create your first DLL — AI generates in 2 minutes      │  │
│  │  2. 📄 Upload class list for auto-fill of SF1                 │  │
│  │  3. 🧮 Set up grading weights for Quarter 1                   │  │
│  │  4. 🤖 Explore the AI Agent Workspace                         │  │
│  │                                                               │  │
│  │  [ ] Show this tour next time                                 │  │
│  │                                                               │  │
│  │  ┌────────────────────────────────┐                           │  │
│  │  │    Go to Dashboard 🚀          │                           │  │
│  │  └────────────────────────────────┘                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Main Dashboard (Teacher Home)

```
┌──────────────┬──────────────────────────────────────────────────────┐
│  [Sidebar]   │  [Search...]                        [🔔] [MR]     │
│  (see nav    │  June 7, 2026 — Friday                                │
│   map)       │  Magandang umaga, Teacher Mariel 👋                  │
│              │  [AI Briefing] [Start LP] [Grading] [Forms] [Ask AI]│
│              ├────────────────────────────┬─────────────────────────┤
│              │  Today's Classes           │ AI Daily Briefing       │
│              │  ┌──────────┬──────────┐   │ ┌─────────────────────┐│
│              │  │ 7:30–8:20│ Math 6   │   │ │ ✓ 3 DLLs ready     ││
│              │  │          │ Sampaguita│  │ │ ⚠ 2 at-risk found  ││
│              │  ├──────────┼──────────┤   │ │ ✓ SF2 92% filled   ││
│              │  │ 8:20–9:10│ Science 6│   │ │ ✓ Parent letters   ││
│              │  │          │ Rosal    │   │ └─────────────────────┘│
│              │  ├──────────┼──────────┤   │  [Open AI Workspace]  │
│              │  │ 9:30–...│ English 6│   └─────────────────────────┘
│              │  └──────────┴──────────┘                             │
│              ├────────────────────────────┬─────────────────────────┤
│              │  Pending Workflows        │ Class Average           │
│              │  ┌────────────────────┐   │ ┌─────────────────────┐│
│              │  │🔴 DLL Math Wed     │   │ │   87.2  ▲ +3.1     ││
│              │  │    LP · due Today  │   │ │   [Chart line]      ││
│              │  │🟡 SF2 Sampaguita  │   │ └─────────────────────┘│
│              │  │    Forms · due Tmrw│  │                         │
│              │  │🟡 Q1 Grades Sci   │   │                         │
│              │  │    Grading · due Fri│ │                         │
│              │  └────────────────────┘   │                         │
│              ├────────────────────────────┴─────────────────────────┤
│              │  At-Risk Students                                    │
│              │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐│
│              │  │ Dela Cruz, J │ │ Santos, A    │ │ Reyes, M     ││
│              │  │ Avg 76 · 72% │ │ Avg 78 · 80% │ │ Avg 74 · 68% ││
│              │  └──────────────┘ └──────────────┘ └──────────────┘│
│              └──────────────────────────────────────────────────────┘
└──────────────────────────────────────────────────────────────────────┘
```

---

## 7. Lesson Planning — Step 1: Input Screen

```
┌──────────────────────────────────────────────────────────────────────┐
│  Lesson Planning Pipeline  [Version history] [Save draft]           │
│  Daily Lesson Log (DLL) Builder                                       │
│                                                                      │
│  [1 ● Input] [2 AI Gen] [3 Review] [4 Export] [5 Archive]          │
│                                                                      │
│  ┌─────────────────────────────────────────┬────────────────────────┐│
│  │  Step 1 · Input                         │  AI Tips              ││
│  │                                         │  ┌──────────────────┐ ││
│  │  [Grade 6 ▾] [Subject ▾] [Quarter ▾]  │  │✨ Select 2-3     │ ││
│  │                                         │  │ MELCs for richest │ ││
│  │  MELC Competencies                      │  │ DLL. You can     │ ││
│  │  ┌────────────────────────────────────┐ │  │ edit after gen.  │ ││
│  │  │ [✓] M6NS-Ia-86 Add/Sub fractions  │ │  └──────────────────┘ ││
│  │  │ [ ] M6NS-Ib-87 Problem solving    │ │                       ││
│  │  │ [✓] M6NS-Ic-90 Multiply fractions │ │                       ││
│  │  └────────────────────────────────────┘ │                       ││
│  │                                         │                       ││
│  │  Duration: [ 60 ] minutes               │                       ││
│  │                                         │                       ││
│  │  ┌─────────────────────────────┐       │                       ││
│  │  │  Continue ▶                 │       │                       ││
│  │  └─────────────────────────────┘       │                       ││
│  └─────────────────────────────────────────┴────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

---

## 8. Lesson Planning — Step 2: AI Generation (Loading State)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Lesson Planning Pipeline                                            │
│  [1 ✓ Input] [2 ● AI Gen] [3 Review] [4 Export] [5 Archive]        │
│                                                                      │
│  ┌─────────────────────────────────────────┬────────────────────────┐│
│  │  Step 2 · AI Generation                 │  AI Tips              ││
│  │                                         │                        ││
│  │  Context: Grade 6 · Math · Q1 · 2 MELCs │                        ││
│  │                                         │                        ││
│  │  [✨ Generating...]                      │                        ││
│  │                                         │                        ││
│  │  [✓] Parsing MELC codes...              │                        ││
│  │  [✓] Matching curriculum guide...       │                        ││
│  │  [✨] Drafting objectives...             │                        ││
│  │  [⏳] Writing procedure...               │                        ││
│  │  [⏳] Creating assessment...             │                        ││
│  │                                         │                        ││
│  │  ┌─────────────────────────────────────┐│                        ││
│  │  │  ████████████████░░░░░░ 65%         ││                        ││
│  │  └─────────────────────────────────────┘│                        ││
│  └─────────────────────────────────────────┴────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

---

## 9. Lesson Planning — Step 3: Review Editor (Split View)

```
┌──────────────────────────────────────────────────────────────────────┐
│  Lesson Planning Pipeline                                            │
│  [1 ✓ Input] [2 ✓ AI Gen] [3 ● Review] [4 Export] [5 Archive]     │
│                                                                      │
│  ┌────────────────────────────────────┬─────────────────────────────┐│
│  │  Step 3 · Review Editor            │  AI Suggestions             ││
│  │  [Improve ▾] [✓ MELC-aligned]     │                              ││
│  │                                     │  ✨ Try this objective:    ││
│  │  📝 I. Objectives (edit) [▶]      │  "Learners will analyze     ││
│  │     At the end of the lesson...    │   real-life fraction uses"  ││
│  │                                     │                              ││
│  │  📝 II. Content (edit) [▶]        │  [Apply suggestion]         ││
│  │                                     │                              ││
│  │  📝 III. Procedure (edit) [▶]     │  ✨ Add differentiation:    ││
│  │     A. Review (5 min)             │  - SPED: visual aids         ││
│  │     B. Purpose (5 min)            │  - Advanced: peer teaching  ││
│  │     C. Examples (10 min)          │                              ││
│  │     D. Guided practice (15 min)   │  [Apply all]                 ││
│  │                                     │                              ││
│  │  📝 IV. Assessment (edit) [▶]     │                              ││
│  │                                     │                              ││
│  │  [Back]              [Continue ▶]  │                              ││
│  └────────────────────────────────────┴─────────────────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

---

## 10. Lesson Planning — Step 4: Export Screen

```
┌──────────────────────────────────────────────────────────────────────┐
│  Lesson Planning Pipeline                                            │
│  [1 ✓] [2 ✓] [3 ✓] [4 ● Export] [5 Archive]                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Step 4 · Export                                              │   │
│  │                                                               │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │   │
│  │  │ 📄 Word    │  │ 📕 PDF     │  │ 📦 Weekly  │             │   │
│  │  │ (.docx)    │  │ (printable)│  │ DLL bundle│             │   │
│  │  │ Download   │  │ Download   │  │ Generate   │             │   │
│  │  │ instantly  │  │ instantly  │  │ all 5 days │             │   │
│  │  └────────────┘  └────────────┘  └────────────┘             │   │
│  │                                                               │   │
│  │  [Back]              [Archive lesson ▶]                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 11. Grading — Step 1: Spreadsheet Data Input

```
┌──────────────────────────────────────────────────────────────────────┐
│  Grading Cycle Engine  [Import Excel] [Save draft]                  │
│  DepEd-weighted quarter grading                                        │
│                                                                      │
│  [1 ● Input] [2 Weights] [3 AI Compute] [4 Analytics] [5 Apprv] [6 Exp]│
│                                                                      │
│  Math 6 — Sampaguita — Quarter 1                                     │
│                                                                      │
│  ┌────────────┬──────┬──────┬──────┬──────┬──────┬────────┐        │
│  │ Student    │ WW1  │ WW2  │ PT1  │ PT2  │ Exam │ Final  │        │
│  ├────────────┼──────┼──────┼──────┼──────┼──────┼────────┤        │
│  │ Dela Cruz  │ 18   │ 20   │ 28   │ 25   │ 45   │ [   ]  │        │
│  │ Santos, A  │ 15   │ 14   │ 22   │ 20   │ 38   │ [   ]  │        │
│  │ Reyes, M   │ 12   │ 10   │ 18   │ 15   │ 30   │ [   ]  │        │
│  │ Bautista   │ 20   │ 19   │ 30   │ 28   │ 48   │ [   ]  │        │
│  │ Gonzales   │ 16   │ 17   │ 25   │ 24   │ 42   │ [   ]  │        │
│  │ ...40 students                                              │        │
│  └────────────┴──────┴──────┴──────┴──────┴──────┴────────┘        │
│                                                                      │
│  [Back]              [Configure Weights ▶]                           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 12. Grading — Step 2: Weight Configuration

```
┌──────────────────────────────────────────────────────────────────────┐
│  Grading Cycle — Weight Configuration                                │
│  [1 ✓ Input] [2 ● Weights] [3 AI Compute] [4 Analytics] [5...]     │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  DepEd Weight Configuration — Grade 6                        │   │
│  │                                                               │   │
│  │  Learning Area: Mathematics                                    │   │
│  │                                                               │   │
│  │  Component              │ Weight    │ Your Scores              │   │
│  │  ──────────────────────────────────────────────               │   │
│  │  Written Works (WW)     │    30%    │ 4 items, max 20         │   │
│  │  Performance Tasks (PT) │    50%    │ 3 items, max 30         │   │
│  │  Quarterly Exam (QE)    │    20%    │ 1 item, max 50          │   │
│  │  ──────────────────────────────────────────────               │   │
│  │  TOTAL                  │   100%    │                         │   │
│  │                                                               │   │
│  │  [Preset: DepEd Standard ▾]  [Custom ▾]                      │   │
│  │                                                               │   │
│  │  ┌────────────────────────────────┐                           │   │
│  │  │  ← Back to Input     [AI Compute ▶]  │                   │   │
│  │  └────────────────────────────────┘                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 13. Grading — Step 3: AI Computation with Error Detection

```
┌──────────────────────────────────────────────────────────────────────┐
│  Grading Cycle — AI Computation                                      │
│  [1 ✓] [2 ✓] [3 ● AI Compute] [4 Analytics] [5...]                 │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Grade Computation Results                                   │   │
│  │                                                               │   │
│  │  [🧮 Compute All Grades]                                      │   │
│  │                                                               │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │  ⚠ Error Detection Panel                                 │ │   │
│  │  │  2 anomalies found:                                      │ │   │
│  │  │  🔴 Reyes, M — PT score (18) exceeds max (30)           │ │   │
│  │  │     [Fix: Cap at 30] [Ignore] [Edit]                    │ │   │
│  │  │  🟡 Bautista — Missing WW2 score                        │ │   │
│  │  │     [Fix: Use 0] [Flag for review] [Edit]               │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  │                                                               │   │
│  │  [← Back]        [View Analytics ▶]                           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 14. Grading — Step 4: Analytics View

```
┌──────────────────────────────────────────────────────────────────────┐
│  Grading Cycle — Analytics                                           │
│  [1 ✓] [2 ✓] [3 ✓] [4 ● Analytics] [5 Approval] [6 Export]        │
│                                                                      │
│  ┌──────────────┬────────────────────┬──────────────────────────┐   │
│  │  Class       │  At-Risk Students  │  Ranking (Top 5)         │   │
│  │  Performance │                    │                          │   │
│  │  [Bar chart] │  ┌──────────────┐ │  1. Bautista, K — 93    │   │
│  │              │  │🟡 Reyes, M  79││  2. Dela Cruz, J — 91   │   │
│  │  95 ┤██      │  │🔴 Santos, A 74││  3. Gonzales, P — 88   │   │
│  │  90 ┤██ ██   │  │🔴 Cruz, L   72││  4. Ramos, M — 86      │   │
│  │  85 ┤██ ██ ██│  └──────────────┘│  5. Torres, N — 85      │   │
│  │  80 ┤██ ██ ██│                    │                          │   │
│  │  75 ┤░░ ██ ██│  [View all →]    │  [View full ranking →]   │   │
│  └──────────────┴────────────────────┴──────────────────────────┘   │
│                                                                      │
│  [← Back]            [Continue to Approval ▶]                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 15. Grading — Step 5: Approval Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│  Grading Cycle — Approval Workflow                                   │
│  [1 ✓] [2 ✓] [3 ✓] [4 ✓] [5 ● Approval] [6 Export]                │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Current Status: [● Draft] [○ Review] [○ Final]              │   │
│  │                                                               │   │
│  │  📋 Summary                                                   │   │
│  │  • 40 students computed                                        │   │
│  │  • 2 manual overrides (Reyes PT, Bautista WW2)                 │   │
│  │  • 2 at-risk students flagged                                  │   │
│  │                                                               │   │
│  │  📅 Timeline                                                   │   │
│  │  • Draft created: Today 10:15 AM                               │   │
│  │  • Last edited: Today 10:45 AM                                 │   │
│  │  • Reviewer: Head Teacher (assigned)                           │   │
│  │                                                               │   │
│  │  [✏️ Continue Editing]  [📤 Submit for Review]  [✓ Finalize]  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 16. School Forms — Form Selection

```
┌──────────────────────────────────────────────────────────────────────┐
│  School Forms Pipeline  [Import LIS] [New batch]                     │
│  Highest Priority Module                                               │
│                                                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │
│  │ SF1    │ │ SF2    │ │ SF5    │ │ SF9    │ │ SF10   │            │
│  │ School │ │ Daily  │ │ Promo  │ │ Learner│ │Perm.   │            │
│  │Registr │ │Attend. │ │ Report │ │Progress│ │Record  │            │
│  │ ✓ Ready│ │🟡 InPrg │ │ Draft  │ │ ✓ Ready│ │ Draft  │            │
│  │        │ │ 92%    │ │        │ │        │ │        │            │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘            │
│                                                                      │
│  [1 ● Data Source] [2 Validation] [3 AI Auto-Fill]                  │
│  [4 Preview] [5 Error Cor] [6 Export & Track]                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 17. School Forms — Validation Dashboard

```
┌──────────────────────────────────────────────────────────────────────┐
│  Forms — Step 2: Validation                                          │
│                                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │ Records found│ │ Warnings     │ │ Errors       │                │
│  │      40      │ │      3       │ │      1       │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                      │
│  Issues Found:                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 🔴 LRN mismatch: J. Santos — LRN has 11 digits (should 12)│   │
│  │    [AI Fix: Append check digit]                             │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ 🟡 Missing father's name: A. Reyes                         │   │
│  │    [AI Fix: Fill "Roberto Reyes" from registration]        │   │
│  ├──────────────────────────────────────────────────────────────┤   │
│  │ 🟡 Attendance mismatch: M. Cruz — 18 vs 17 days            │   │
│  │    [AI Fix: Use register count 18 per DO 8 s.2015]         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  [Proceed with warnings ▶]                                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 18. Student Profile — With Intervention Panel

```
┌──────────────────────────────────────────────────────────────────────┐
│  Student: Dela Cruz, Juan  [LRN 137020025488]     [HIGH RISK 🔴]   │
│  Gr 6 · Sampaguita · Guardian: Mrs. Dela Cruz · +639123456789      │
│                                                                      │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐                      │
│  │ Avg Grade  │ │ Attendance │ │ Behavior   │                      │
│  │    76     │ │    72%    │ │   2 notes  │                      │
│  │  ▼ -3 pts │ │  ▼ -8%    │ │            │                      │
│  └────────────┘ └────────────┘ └────────────┘                      │
│                                                                      │
│  ┌─── AI Intervention Suggestions ──────────────────────────────┐   │
│  │  ✨ Schedule 1-on-1 remediation in Math (fractions)          │   │
│  │  ✨ Send Tagalog letter about 3 unexcused absences           │   │
│  │  ✨ Pair with high-achieving learner for next group activity  │   │
│  │  [Open case] [Draft letter]                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─── Case Management ──────────────────────────────────────────┐   │
│  │  Issue: Drop in Q1 Math grade (89 → 78)                     │   │
│  │  Action: Remediation + parent notice                        │   │
│  │  Status: 🟡 In progress                                     │   │
│  │  Next review: Friday, Sept 27                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 19. Parent Communication — Message Generator

```
┌──────────────────────────────────────────────────────────────────────┐
│  Parent Communication — Message Generator                            │
│                                                                      │
│  ┌───────┬──────────────────────────────────────────────────────┐   │
│  │ Select│ [Dela Cruz, Juan ▾]                                  │   │
│  │Student├──────────────────────────────────────────────────────┤   │
│  │       │ Issue: [Absence ▾]  Sub: [3 consecutive days]       │   │
│  ├───────┴──────────────────────────────────────────────────────┤   │
│  │  ✨ AI Message Draft                                         │   │
│  │  ┌──────────────────────────────────────────────────────────┐│   │
│  │  │  Greeting: [Formal Tagalog ▾]                            ││   │
│  │  │                                                          ││   │
│  │  │  Mahal naming Ginoong/Ginang Dela Cruz,                 ││   │
│  │  │                                                          ││   │
│  │  │  Kami po ay sumusulat upang ipaalam na ang inyong      ││   │
│  │  │  anak na si Juan ay hindi po pumasok noong Setyembre    ││   │
│  │  │  23, 24, at 25. Ito ay kanyang ika-3, 4, at 5 na       ││   │
│  │  │  pagliban ngayong buwan.                                 ││   │
│  │  │                                                          ││   │
│  │  │  Maaari po ba kayong makipagkita sa amin para           ││   │
│  │  │  sa isang conference?                                   ││   │
│  │  │                                                          ││   │
│  │  │  [Regenerate] [Edit] [Use as SMS] [Use as Messenger]    ││   │
│  │  └──────────────────────────────────────────────────────────┘│   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─── Communication History ────────────────────────────────────┐   │
│  │  Sep 20 → SMS sent: "Reminder: Parent meeting Friday 3PM"   │   │
│  │  Sep 15 → Messenger: "Grade update — Science quiz result"   │   │
│  │  Sep 10 → Letter sent: "Regarding Juan's behavior"          │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 20. Reports — AI Builder

```
┌──────────────────────────────────────────────────────────────────────┐
│  Reports & Compliance — AI Report Builder                            │
│                                                                      │
│  Template: [RPMS Sy 2026-2027 ▾]  Period: [Quarter 1 ▾]           │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Input the required info for the AI to draft your report:     │   │
│  │                                                               │   │
│  │  Key accomplishments: [___________________________________]  │   │
│  │  Challenges faced: [______________________________________]   │   │
│  │  Interventions applied: [_________________________________]   │   │
│  │                                                               │   │
│  │  [Attach evidence files] [📎 Drag & drop files here]          │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │  📄 DLL_Week4_Math.pdf  ✓                                │ │   │
│  │  │  🖼️ Class_Photo_SciFair.jpg  ✓                          │ │   │
│  │  │  📊 Quiz_Results_Q1.xlsx  ✓                              │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  │                                                               │   │
│  │  [✨ Generate Report with AI]                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 21. School Programs — Gantt-style Planner

```
┌──────────────────────────────────────────────────────────────────────┐
│  School Programs — Feeding Program                                   │
│                                                                      │
│  ┌──── Status ──────────────────────────────────────────────────┐   │
│  │  [● Planning] [○ Execution] [○ Reporting] [○ Completed]     │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Timeline View (Gantt)                                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Task                    │ Sep W1 │ W2 │ W3 │ W4 │ Oct W1  │   │
│  │  ─────────────────────────────────────────────────────────── │   │
│  │  Needs Assessment        │ ████   │    │    │    │          │   │
│  │  Menu Planning           │        │ ████│    │    │          │   │
│  │  Parent Permission Slips │        │    │ ████│    │          │   │
│  │  Food Preparation        │        │    │    │ ████│          │   │
│  │  Feeding Implementation  │        │    │    │    │ ████████ │   │
│  │  Post-Program Report     │        │    │    │    │          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌── Budget ────────────────────────────────────────────────────┐   │
│  │  Item               │ Qty  │ Amount │ Total                   │   │
│  │  Rice (50kg)        │  2   │ 2,500  │ 5,000                  │   │
│  │  Chicken (kg)       │  15  │ 180    │ 2,700                  │   │
│  │  Vegetables (assort)│  —   │  —     │ 1,500                  │   │
│  │  Cooking supplies   │  —   │  —     │ 800                    │   │
│  │  ─────────────────────────────────────────────               │   │
│  │  TOTAL:                                       ₱10,000        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 22. AI Assistant Sidebar (Global Persistent)

```
┌──────────────────────────────────────────────────────────────────────┐
│  [Main Content Area...]                    ┌────────────────────┐   │
│                                              │  ✨ AI Assistant   │   │
│                                              │                    │   │
│                                              │  Context: 📘       │   │
│                                              │  Lesson Planning   │   │
│                                              │  Page              │   │
│                                              │                    │   │
│                                              │  [🔗 Use this      │   │
│                                              │   screen's data]   │   │
│                                              │                    │   │
│                                              │  ─── Quick Actions │   │
│                                              │  [Fix errors]      │   │
│                                              │  [Generate report] │   │
│                                              │  [Summarize page]  │   │
│                                              │                    │   │
│                                              │  ─── Recent Memory │   │
│                                              │  ✓ DLL for Math 6 │   │
│                                              │  ✓ SF2 validation  │   │
│                                              │  ⏳ Grade compute  │   │
│                                              │                    │   │
│                                              │  ┌────────────────┐│   │
│                                              │  │ Type a message ││   │
│                                              │  │ or ask me...  ││   │
│                                              │  └────────────────┘│   │
│                                              └────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 23. Mobile Responsive — Dashboard

```
┌─────────────────────────────────────┐
│  [🧠 TeachOS]  [🔍]  [🔔]  [👤]  │
├─────────────────────────────────────┤
│                                     │
│  Good morning, Teacher Mariel!      │
│  3 pending · 5 classes today        │
│                                     │
│  ┌── Quick Actions ──────────────┐ │
│  │ 📘 Lesson Plan  🧮 Grading   │ │
│  │ 📄 Forms       🤖 Ask AI     │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌── AI Briefing ────────────────┐ │
│  │ ✓ 3 DLLs ready                │ │
│  │ ⚠ 2 at-risk students          │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌── Today's Classes ────────────┐ │
│  │ 🕐 7:30 Math 6 · Sampaguita  │ │
│  │    [▶ Start lesson]           │ │
│  ├───────────────────────────────┤ │
│  │ 🕐 8:20 Science 6 · Rosal    │ │
│  └───────────────────────────────┘ │
│                                     │
│  ┌── Pending Tasks ─────────────┐ │
│  │ 🔴 DLL Math Wed — due Today  │ │
│  │ 🟡 SF2 — due Tomorrow        │ │
│  └───────────────────────────────┘ │
├─────────────────────────────────────┤
│  🏠 Home  📘 LP  🧮 Grad  📄 Forms│
│  🤖 AI                              │
└─────────────────────────────────────┘
```

---

## 24. Mobile Responsive — Lesson Planning

```
┌─────────────────────────────────────┐
│  [←] Lesson Planning    [💾] [⋯]   │
├─────────────────────────────────────┤
│                                     │
│  [1 ● Input] [2 ○] [3 ○]           │
│  ████████░░░░░░░░ 40%               │
│                                     │
│  Grade: [6 ▾]  Subject: [Math ▾]   │
│  Quarter: [Q1 ▾]                    │
│                                     │
│  MELC Competencies                  │
│  ┌────────────────────────────────┐ │
│  │ ✓ M6NS-Ia-86 Add fractions    │ │
│  │ ○ M6NS-Ib-87 Problem solving  │ │
│  │ ✓ M6NS-Ic-90 Multiply fract   │ │
│  └────────────────────────────────┘ │
│                                     │
│  Duration: [ 60 ] min               │
│                                     │
│  ┌──────────────────────────────┐   │
│  │       Continue ▶             │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 25. Tablet Responsive — Grading Spreadsheet

```
┌──────────┬───────────────────────────────────────────────────────┐
│ [≡]      │  Grading Cycle — Grade 6 Math — Sampaguita           │
│ Icons    │  [Step 1 ●] [2 ○] [3 ○] [4 ○] [5 ○]                 │
│          ├───────────────────────────────────────────────────────┤
│ 🏠       │  ┌──────┬────┬────┬────┬────┬──────┬──────┐         │
│ 📅       │  │Student│ WW1│ WW2│ PT1│ PT2│ Exam │Final│         │
│ 📘 ▶    │  ├──────┼────┼────┼────┼────┼──────┼──────┤         │
│ 🧮       │  │D.Cruz│ 18 │ 20 │ 28 │ 25 │ 45   │      │         │
│ 📄       │  │Santos│ 15 │ 14 │ 22 │ 20 │ 38   │      │         │
│ 👥       │  │Reyes │ 12 │ 10 │ 18 │ 15 │ 30   │      │         │
│ 💬       │  │...and 37 more rows...   │      │         │
│ 📊       │  └──────┴────┴────┴────┴────┴──────┴──────┘         │
│ 🏫       │                                                       │
│ 🤖       │  [← Back]        [Configure Weights ▶]               │
│ ⚙️       │                                                       │
└──────────┴───────────────────────────────────────────────────────┘