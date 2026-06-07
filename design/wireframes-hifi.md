# TeacherOS — High-Fidelity Wireframes (SaaS-Style UI Mockups)

## Design System Tokens (Applied Throughout)

| Token | Value | Usage |
|-------|-------|-------|
| Primary | `#2563eb` (blue) | Buttons, links, active states, icons |
| Primary Soft | `#eef2ff` | Card backgrounds, active rows |
| Success | `#16a34a` | Completed, synced, healthy |
| Warning | `#d97706` | In-progress, pending action |
| Destructive | `#dc2626` | Errors, at-risk, overdue |
| Sidebar BG | `#f8fafc` | Dark sidebar background |
| Border | `#e2e8f0` | Card borders, table borders |
| Font | Inter (UI), Plus Jakarta Sans (display) |
| Radius | 0.75rem (12px) |
| Shadow | `0 1px 2px rgba(0,0,0,0.04), 0 8px 24px -8px rgba(0,0,0,0.1)` |

---

## 1. Login Screen — High-Fidelity

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                    ┌─────────────────────────────────────────┐          │
│                    │                                         │          │
│                    │     ┌──────────────────────┐            │          │
│                    │     │  🧠                   │            │          │
│                    │     │                       │            │          │
│                    │     │  TeacherOS            │            │          │
│                    │     │  Philippines          │            │          │
│                    │     │                       │            │          │
│                    │     │  AI Operating System   │            │          │
│                    │     │  for Teachers          │            │          │
│                    │     └──────────────────────┘            │          │
│                    │                                         │          │
│                    │  ┌─────────────────────────────────┐    │          │
│                    │  │ 📧 DepEd Email Address or LRN   │    │          │
│                    │  └─────────────────────────────────┘    │          │
│                    │                                         │          │
│                    │  ┌─────────────────────────────────┐    │          │
│                    │  │ 🔒 Password                      │    │          │
│                    │  └─────────────────────────────────┘    │          │
│                    │                                         │          │
│                    │  ┌─────────────────────────────┐        │          │
│                    │  │    Sign In                  │        │          │
│                    │  └─────────────────────────────┘        │          │
│                    │                                         │          │
│                    │  ── or continue with ──                  │          │
│                    │                                         │          │
│                    │  [Google] [Microsoft] [DepEd SSO]      │          │
│                    │                                         │          │
│                    │  Don't have an account? [Sign up free]  │          │
│                    └─────────────────────────────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

Design Notes:
- Full-screen centered card on gradient bg (#f0f4ff to #ffffff)
- Card: white, 420px max-width, shadow-elegant, rounded-2xl
- Logo area: 48px icon + title, centered
- Inputs: 40px height, border-input, rounded-md, focus-ring primary
- CTA button: primary bg, white text, 40px height, full width
- SSO buttons: outlined, icon + text
- Link color: primary blue
```

---

## 2. Onboarding Wizard — High-Fidelity

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                    ┌─────────────────────────────────────────┐          │
│                    │  [Back]  Setup Wizard                [Skip] │      │
│                    │                                         │          │
│                    │  Step 1 of 4: Tell us about you          │          │
│                    │  ●─────────────────────────○             │          │
│                    │  Progress: 25%                          │          │
│                    │                                         │          │
│                    │  What is your role?                      │          │
│                    │                                         │          │
│                    │  ┌────────────┐  ┌────────────┐         │          │
│                    │  │ 👤          │  │ 👥          │         │          │
│                    │  │ Subject    │  │ Class      │         │          │
│                    │  │ Teacher    │  │ Adviser    │         │          │
│                    │  │            │  │            │         │          │
│                    │  │ Teaches    │  │ Manages 1  │         │          │
│                    │  │ multiple   │  │ class      │         │          │
│                    │  └────────────┘  └────────────┘         │          │
│                    │                                         │          │
│                    │  ┌────────────┐  ┌────────────┐         │          │
│                    │  │ 📋          │  │ 🏫          │         │          │
│                    │  │ Program    │  │ Master     │         │          │
│                    │  │ Coordinator│  │ Teacher    │         │          │
│                    │  └────────────┘  └────────────┘         │          │
│                    │                                         │          │
│                    │  Grade level(s):                         │          │
│                    │  [1] [2] [3] [4] [5] [6] [7] [8] [9] [10]  │       │
│                    │                                         │          │
│                    │  ┌─────────────────────────────┐        │          │
│                    │  │        Continue →           │        │          │
│                    │  └─────────────────────────────┘        │          │
│                    └─────────────────────────────────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

Design Notes:
- Card: 640px max-width, white, shadow-elegant, rounded-2xl
- Role cards: 160px wide, icon 32px, border, hover:primary-border
- Selected role: primary border + primary-soft bg
- Grade pills: toggleable chips, selected = primary bg
- Progress bar: thin, primary fill, 4 segments
```

---

## 3. Main Dashboard — High-Fidelity (Desktop)

```
┌──────────────┬─────────────────────────────────────────────────────────────────┐
│ [SIDEBAR]   │  ┌─────────────────────────────────────────────────────────┐    │
│              │  │  🔍 Search students, lessons, forms...    [🔔]  [👤 MR]│    │
│              │  ├─────────────────────────────────────────────────────────┤    │
│              │  │                                                         │    │
│              │  │  DASHBOARD                                              │    │
│              │  │  June 7, 2026 — Friday                                   │    │
│              │  │                                                         │    │
│              │  │  Magandang umaga, Teacher Mariel 👋                     │    │
│              │  │  5 classes today · 3 pending workflows                  │    │
│              │  │                                                         │    │
│              │  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │    │
│              │  │  │ 📘 Lesson   │ │ 🧮 Grading  │ │ 📄 Forms     │    │    │
│              │  │  │ Planning    │ │              │ │              │    │    │
│              │  │  │ Start new   │ │ Continue Q1  │ │ SF2 needs    │    │    │
│              │  │  │ lesson plan │ │ grade comp   │ │ attendance   │    │    │
│              │  │  └──────────────┘ └──────────────┘ └──────────────┘    │    │
│              │  │                                                         │    │
│              │  │  ┌──────────────┐ ┌────────────────────────────────┐  │    │
│              │  │  │ Today's     │ │ AI Daily Briefing               │  │    │
│              │  │  │ Schedule    │ │                                 │  │    │
│              │  │  │             │ │ ✓ 3 DLLs ready for Math 6     │  │    │
│              │  │  │ 7:30 Math 6 │ │   Week 4                       │  │    │
│              │  │  │    Sampaguita │ │ ⚠ 2 students dropped >5%    │  │    │
│              │  │  │ 8:20 Science│ │   Interventions ready          │  │    │
│              │  │  │ 9:30 Eng    │ │ ✓ SF2 Sept 92% auto-filled    │  │    │
│              │  │  │ 10:20 AP    │ │ ✓ Parent letters (3) ready    │  │    │
│              │  │  │ 1:00 MAPEH  │ └────────────────────────────────┘  │    │
│              │  │  └──────────────┘                                     │    │
│              │  │                                                         │    │
│              │  │  ┌───────────────────────────────────┐                │    │
│              │  │  │ Pending Workflows                 │                │    │
│              │  │  │                                   │                │    │
│              │  │  │ 🔴 DLL Math 6 — Wed        LP    │                │    │
│              │  │  │    Due: Today [Resume]            │                │    │
│              │  │  │ 🟡 SF2 Attendance          Forms  │                │    │
│              │  │  │    Due: Tomorrow [Resume]         │                │    │
│              │  │  │ 🟡 Q1 Grades Science      Grading │                │    │
│              │  │  │    Due: Friday [Resume]           │                │    │
│              │  │  └───────────────────────────────────┘                │    │
│              │  │                                                         │    │
│              │  │  ┌────────────────────────────────────────────────────┐ │    │
│              │  │  │ At-Risk Students                                   │ │    │
│              │  │  │ ┌──────────┐ ┌──────────┐ ┌──────────┐          │ │    │
│              │  │  │ │Del.Cruz,J│ │Santos,A  │ │Reyes,M   │          │ │    │
│              │  │  │ │Avg 76    │ │Avg 78    │ │Avg 74    │          │ │    │
│              │  │  │ │Att 72%   │ │Att 80%   │ │Att 68%   │          │ │    │
│              │  │  │ │🔴 High   │ │🟡 Med    │ │🔴 High   │          │ │    │
│              │  │  │ └──────────┘ └──────────┘ └──────────┘          │ │    │
│              │  │  └────────────────────────────────────────────────────┘ │    │
│              │  └─────────────────────────────────────────────────────────┘    │
└──────────────┴─────────────────────────────────────────────────────────────────┘

Component Specs:
- Quick Action Cards: 1fr each, icon 36px circle (tinted bg), title semibold, subtitle muted
- Schedule Item: 48px row, time col (mono 12px), subject 14px, section 12px, NEXT badge (success)
- AI Briefing Card: gradient border (primary/30), icon 32px gradient, checklist items 13px
- Pending Workflows: severity dot (8px), title 14px, module+due 12px, Resume btn outline-sm
- At-Risk Cards: avatar 36px circle, avg+att text, risk badge
```

---

## 4. Lesson Planning — Step 3 Review Editor (High-Fi)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [SIDEBAR]   │  Lesson Planning Pipeline  [History] [💾 Save]          │
│              │                                                         │
│              │  Daily Lesson Log (DLL) Builder — Grade 6 · Math · Q1   │
│              │                                                         │
│              │  [1 ✓ Input] [2 ✓ AI Gen] [3 ● Review] [4 Export] [5 Archive] │
│              │                                                         │
│              │  ┌─────────────────────────────────┬──────────────────┐  │
│              │  │  Review Editor                  │  AI Suggestions   │  │
│              │  │                                 │                   │  │
│              │  │  [Improve ▾] [🔍]               │  ✨ Try:          │  │
│              │  │                                 │                   │  │
│              │  │  ▸ I. Objectives                │  "Learners will   │  │
│              │  │     At the end of the lesson... │   analyze real-   │  │
│              │  │     (click to edit)             │   life fractions" │  │
│              │  │                                 │                   │  │
│              │  │  ▸ II. Content                  │  [Apply]          │  │
│              │  │     Subject Matter...           │                   │  │
│              │  │                                 │  ✨ Differentiate: │  │
│              │  │  ▸ III. Procedure               │  • SPED: visual   │  │
│              │  │     A. Review (5 min)           │  • Advanced: peer │  │
│              │  │     B. Purpose (5 min)          │  teaching          │  │
│              │  │     C. Examples (10 min)        │                   │  │
│              │  │     D. Practice (15 min)        │  [Apply all]      │  │
│              │  │     E. Generalization (5 min)   │                   │  │
│              │  │                                 │  ────              │  │
│              │  │  ▸ IV. Assessment               │  🧠 Context        │  │
│              │  │     ...                          │  Grade 6 · Math   │  │
│              │  │                                 │  Q1 · 2 MELCs     │  │
│              │  │  [← Back]    [Continue →]       │  Past DLLs: 12    │  │
│              │  └─────────────────────────────────┴──────────────────┘  │
│              │                                                         │
│              │  ✓ Autosaved · 10:23 AM                                │
│              └─────────────────────────────────────────────────────────┘

Component Specs:
- Split Panel: 2/3 editor, 1/3 suggestions (resizable)
- Collapsible sections: chevron icon, hover bg, pre body
- AI Suggestions card: primary-soft bg, border-l-4 primary
- Apply buttons: small, primary outline
- Status bar: fixed bottom-left, success icon + text
```

---

## 5. Grading Spreadsheet (High-Fi Data Grid)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Grading Cycle Engine  [📥 Import Excel] [💾 Save]                     │
│                                                         │
│  Grade 6 · Math · Sampaguita · Quarter 1                               │
│                                                         │
│  [1 ● Input] [2 Weights] [3 AI Compute] [4 Analytics] [5 Approval] [6 Export] │
│                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  # │ Student           │ WW1 │ WW2 │ PT1 │ PT2 │ Exam │ 💯      │  │
│  │    │                   │ 20  │ 20  │ 30  │ 30  │ 50   │ Final   │  │
│  ├────┼───────────────────┼─────┼─────┼─────┼─────┼──────┼─────────┤  │
│  │  1 │ Dela Cruz, Juan  │ 18  │ 20  │ 28  │ 25  │ 45   │ 87.5    │  │
│  │  2 │ Santos, Anna     │ 15  │ 14  │ 22  │ 20  │ 38   │ 75.8    │  │
│  │  3 │ Reyes, Mario     │ 12  │ 10  │ 18🔴│ 15  │ 30   │ 68.3⚠   │  │
│  │  4 │ Bautista, K.     │ 20  │ 19  │ 30  │ 28  │ 48   │ 93.1    │  │
│  │  5 │ Gonzales, P.     │ 16  │ 17  │ 25  │ 24  │ 42   │ 83.4    │  │
│  │  6 │ Ramos, M.        │ 14  │ 15  │ 20  │ 22  │ 35   │ 72.9    │  │
│  │  ... (40 rows)                                                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                         │
│  Summary: 40 students · Avg 82.3 · 2 at-risk · 1 anomaly              │
│                                                         │
│  [← Back]              [Configure Weights →]                           │
│                                                         │
└─────────────────────────────────────────────────────────────────────────┘

Component Specs:
- Data Grid: sticky header, alternating row bg, editable cells (on click)
- Column headers: uppercase 10px, muted, max in sub-label
- Cell: 44px min height, border, focus ring on edit
- Anomaly cell: red bg tint, tooltip "Exceeds max"
- Score cell: final grade bold, <75 gets warning icon
- Summary bar: sticky footer, stats in muted text
```

---

## 6. School Forms — DepEd SF2 Preview (High-Fi)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  SF2 — DAILY ATTENDANCE REPORT OF LEARNERS  [🔍 Find] [✏️ Edit]      │
│                                                                         │
│  Republic of the Philippines                                            │
│  DEPARTMENT OF EDUCATION                                                │
│  Region III · Division of Bulacan · Sampaloc Elementary School         │
│  School Year 2026–2027 · September · Grade 6 — Sampaguita             │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ # │ LEARNER'S NAME         │ LRN          │ S │ 1 2 3 4 5...│TOT│  │
│  ├────┼───────────────────────┼──────────────┼───┼──────────────┼───┤  │
│  │ 1  │ Dela Cruz, Juan      │137020025488  │ M │ ✓ ✓ ✓ ✓ ✓   │ 20│  │
│  │ 2  │ Santos, Anna         │137020025489  │ F │ ✓ ✓ ✗ ✓ ✓   │ 19│  │
│  │ 3  │ Reyes, Mario         │137020025490  │ M │ ✓ ✓ ✓ ✓ ✓   │ 20│  │
│  │ 4  │ Bautista, K.         │137020025491  │ F │ ✓ ✓ ✓ ✓ ✓   │ 20│  │
│  │ 5  │ Gonzales, P.         │137020025492  │ M │ ✓ ✗ ✗ ✓ ✓   │ 18│  │
│  │ 6  │ Ramos, M.            │137020025493  │ F │ ✓ ✓ ✓ ✓ ✓   │ 20│  │
│  │ 7  │ Castillo, L.         │137020025494  │ M │ ✗ ✗ ✓ ✓ ✓   │ 17│  │
│  │ 8  │ Cruz, A.             │137020025495  │ F │ ✓ ✓ ✓ ✓ ✓   │ 20│  │
│  │ 9  │ Torres, N.           │137020025496  │ M │ ✓ ✓ ✓ ✓ ✓   │ 20│  │
│  │ 10 │ Flores, M.           │137020025497  │ F │ ✓ ✓ ✗ ✓ ✓   │ 19│  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ✨ AI detected: 1 LRN format issue, 2 attendance mismatches            │
│  [View errors] [Download PDF] [Submit to Principal]                    │
└─────────────────────────────────────────────────────────────────────────┘

Design Notes:
- Serif font family for DepEd-form authenticity
- Exact 1px solid borders, uppercase headers
- Check/cross marks for attendance
- Red highlighted cells for errors
- Sticky first column (name) on horizontal scroll
- Print-optimized: 8.5in x 14in aspect ratio
```

---

## 7. AI Assistant Sidebar (High-Fi)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  [MAIN CONTENT]                           ┌─────────────────────────┐  │
│                                              │  ✨ AI Assistant       │  │
│                                              │                       │  │
│                                              │  📘 Context:          │  │
│                                              │  Lesson Planning      │  │
│                                              │  Page                 │  │
│                                              │                       │  │
│                                              │  🔗 [Use this page's  │  │
│                                              │      context]         │  │
│                                              │                       │  │
│                                              │  ─── Quick Actions    │  │
│                                              │                       │  │
│                                              │  ┌─────────────────┐  │  │
│                                              │  │ 🔧 Fix errors   │  │  │
│                                              │  └─────────────────┘  │  │
│                                              │  ┌─────────────────┐  │  │
│                                              │  │ 📊 Gen report   │  │  │
│                                              │  └─────────────────┘  │  │
│                                              │  ┌─────────────────┐  │  │
│                                              │  │ 📋 Summarize    │  │  │
│                                              │  └─────────────────┘  │  │
│                                              │                       │  │
│                                              │  ─── Recent Memory    │  │
│                                              │  ✓ DLL Math 6 Wk4    │  │
│                                              │  ○ SF2 validation     │  │
│                                              │  ○ Grade computing    │  │
│                                              │                       │  │
│                                              │  ┌──────────────────┐ │  │
│                                              │  │ Type a message   │ │  │
│                                              │  │ or ask me...    │ │  │
│                                              │  └──────────────────┘ │  │
│                                              │                       │  │
│                                              │  [AI is responding...] │  │
│                                              └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

Component Specs:
- Width: 320px on desktop, 280px on tablet
- Slide-in animation: 200ms ease
- Header: icon + title + close button
- Context chip: primary-soft bg, small text
- Quick action buttons: full width, text + icon, outline style
- Memory panel: checkmark for done, circle for pending
- Chat input: 36px height, rounded-lg, with send icon
- Scroll overflow for long content
```

---

## 8. Mobile Bottom Navigation (High-Fi)

```
┌─────────────────────────────────────────────────────────────────┐
│  [Content Area - full width]                                    │
│                                                                 │
│                                                                 │
│                                                                 │
│                                                                 │
│                                                                 │
│                                                                 │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐            │
│  │ 🏠   │  │ 📘   │  │ 🧮   │  │ 📄   │  │ 🤖   │            │
│  │ Home │  │ LP   │  │ Grad │  │ Forms│  │ AI   │            │
│  │ ●    │  │      │  │      │  │      │  │      │            │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘            │
└─────────────────────────────────────────────────────────────────┘

Design Notes:
- Height: 64px safe area
- Active tab: primary icon + dot indicator
- Inactive: muted foreground
- Safe area inset for notched phones
- Icons: 24px, labels: 10px semibold
- Swipe gesture support between tabs
```

---

## 9. Programs — Gantt Chart (High-Fi)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  School Programs — Feeding Program  [Edit] [Export]                    │
│                                                                         │
│  Status: [● Planning] [○ Execution] [○ Reporting] [○ Completed]        │
│                                                                         │
│  ┌─────┬───────────────────────────────────────────────────────────┐   │
│  │ Task │ Sep W1     │ Sep W2     │ Sep W3     │ Sep W4     │ Oct  │   │
│  ├─────┼───────────────────────────────────────────────────────────┤   │
│  │ Need │ ████████    │            │            │            │     │   │
│  │ Assm  │ Done        │            │            │            │     │   │
│  ├─────┼─────────────┼────────────┼────────────┼────────────┼─────┤   │
│  │ Menu │            │ ████████   │            │            │     │   │
│  │ Plan │            │ In Progress│            │            │     │   │
│  ├─────┼─────────────┼────────────┼────────────┼────────────┼─────┤   │
│  │ Par- │            │            │ ░░░░░░░░   │            │     │   │
│  │ ent  │            │            │ Pending    │            │     │   │
│  │ Per- │            │            │            │            │     │   │
│  │ miss │            │            │            │            │     │   │
│  └─────┴─────────────┴────────────┴────────────┴────────────┴─────┘   │
│                                                                         │
│  ┌── Budget Breakdown ────────────────────────────────────────────┐   │
│  │ Item                  │ Qty  │ Unit Cost │ Total                │   │
│  │ Rice (50kg sack)      │  2   │ ₱2,500   │ ₱5,000              │   │
│  │ Chicken (whole, kg)   │ 15   │ ₱180     │ ₱2,700              │   │
│  │ Vegetables (assorted)  │  1   │ ₱1,500   │ ₱1,500              │   │
│  │ Cooking supplies       │  1   │ ₱800     │ ₱800                │   │
│  ├────────────────────────────────────────────────────────────────┤   │
│  │ TOTAL BUDGET                          │ ₱10,000               │   │
│  │ MOOE ALLOCATION                       │ ₱15,000               │   │
│  │ REMAINING                             │ ₱5,000                │   │
│  └────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘

Component Specs:
- Gantt row: 48px height, task name left, bar right
- Bar colors: blue (done), yellow (in-progress), dashed (pending)
- Week columns: 100px each, with date header
- Budget table: number formatting, total row bold bg
- Progress indicator: % complete per task
```

---

## 10. Parent Communication — SMS/Messenger Preview (High-Fi)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Parent Communication — Message Preview                                │
│                                                                         │
│  Student: Dela Cruz, Juan · Issue: Absence (3 consecutive days)        │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │  Preview mode: [● SMS] [○ Messenger] [○ Printable]    │           │
│  └─────────────────────────────────────────────────────────┘           │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────┐           │
│  │  SMS View (Mobile Frame)                                │           │
│  │  ┌──────────────────────────────────────────────────┐   │           │
│  │  │  📱 T. Mariel Reyes                   3:45 PM    │   │           │
│  │  │                                                │   │           │
│  │  │  ┌────────────────────────────────────────┐    │   │           │
│  │  │  │ Gng. Dela Cruz,                        │    │   │           │
│  │  │  │                                        │    │   │           │
│  │  │  │ Ito po ay paalala mula sa Sampaloc    │    │   │           │
│  │  │  │ Elementary School. Ang inyong anak    │    │   │           │
│  │  │  │ na si Juan ay hindi po pumasok ng     │    │   │           │
│  │  │  │ 3 araw (Sep 23-25).                    │    │   │           │
│  │  │  │                                        │    │   │           │
│  │  │  │ Maaari po ba kayong mag-conference    │    │   │           │
│  │  │  │ sa paaralan?                           │    │   │           │
│  │  │  │                                        │    │   │           │
│  │  │  │ Salamat po.                           │    │   │           │
│  │  │  └────────────────────────────────────────┘    │   │           │
│  │  └──────────────────────────────────────────────────┘   │           │
│  │                                                         │           │
│  │  [✏️ Edit] [Regenerate] [Send Now] [Schedule]          │           │
│  │                                                         │           │
│  │  Language: [Tagalog ▾]  Tone: [Formal ▾]               │           │
│  └─────────────────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘

Design Notes:
- Phone frame: 280px wide, rounded corners, subtle shadow
- Message bubble: rounded-lg, primary-soft bg, text 13px
- Timestamp: muted, 11px, right-aligned
- Language/Tone selector: compact dropdowns
- Send button: primary solid, Schedule: outline secondary
- Country code: +63 (Philippines) auto-filled
```

---

## 11. Reports — Evidence Upload Panel (High-Fi)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Reports & Compliance — Attach Evidence                                 │
│                                                                         │
│  Report: RPMS Sy 2026-2027 · Q1 · Teacher Mariel Reyes                │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  📎 Drag & drop files here, or click to browse                   │  │
│  │                                                                  │  │
│  │  Supported: PDF, DOCX, JPG, PNG, XLSX (Max 20MB each)           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  Uploaded Evidence (3 files):                                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │ 📄 DLL_Week4_Math.pdf     2.4 MB                    [🗑️] │  │  │
│  │  │   Uploaded: Today 10:30 AM · Linked to: Math 6 Wk4         │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │ 🖼️ Science_Fair_Photos.zip  8.1 MB                   [🗑️] │  │  │
│  │  │   Uploaded: Today 10:32 AM · 12 photos                     │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │ 📊 Quiz_Results_Q1.xlsx    1.1 MB                     [🗑️] │  │  │
│  │  │   Uploaded: Today 10:35 AM · 40 students                   │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  [← Back to Draft]              [Generate Final Report]                │
└─────────────────────────────────────────────────────────────────────────┘

Component Specs:
- Drop zone: dashed border, 120px height, hover: primary border, icon centered
- File item: 64px row, icon (filetype-specific color), name, size, date, delete btn
- Progress bar for uploading: animated gradient
- Auto-tagging: AI suggests links to existing modules
```

---

## 12. User Profile — Full Student Intelligence View (High-Fi)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🧑 Student Intelligence Hub  [Run Risk Scan]                         │
│                                                                         │
│  ┌── Student List (40) ──────────┬── Profile: Dela Cruz, Juan ───────┐│
│  │ 🔍 Search learner...          │                                    ││
│  │                               │  LRN 137020025488                  ││
│  │ ┌───────────────────────────┐ │  Grade 6 · Sampaguita             ││
│  │ │ 👤 Dela Cruz, Juan   76📉│ │  Guardian: Mrs. Dela Cruz         ││
│  │ │ 👤 Santos, Anna      78🟡│ │  Contact: +639123456789            ││
│  │ │ 👤 Reyes, Mario      74🔴│ │                                    ││
│  │ │ 👤 Bautista, K.      93📈│ │  ┌──────┐ ┌──────┐ ┌──────┐     ││
│  │ │ 👤 Gonzales, P.      83📈│ │  │ 76   │ │ 72%  │ │ 2    │     ││
│  │ │ 👤 Ramos, M.         72🔴│ │  │ Avg  │ │ Att  │ │ Notes│     ││
│  │ │ 👤 Castillo, L.      85📈│ │  │ ▼3pts│ │ ▼8%  │ │      │     ││
│  │ │ ...                        │  └──────┘ └──────┘ └──────┘     ││
│  │ └───────────────────────────┘ │                                    ││
│  │                               │  ✨ AI Intervention Suggestions    ││
│  │ Filters:                      │  ┌──────────────────────────────┐ ││
│  │ [All] [At-risk] [Achievers]   │  │ 1. Schedule 1-on-1 Math     │ ││
│  │ [Attendance]                  │  │    remediation (fractions)   │ ││
│  │                               │  │ 2. Send Tagalog letter re: 3 │ ││
│  │                               │  │    unexcused absences        │ ││
│  │                               │  │ 3. Pair with high-achiever   │ ││
│  │                               │  │    for next group activity   │ ││
│  │                               │  └──────────────────────────────┘ ││
│  │                               │  [Open case] [Draft letter]      ││
│  └───────────────────────────────┴────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘