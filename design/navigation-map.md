# TeacherOS Navigation Structure Map

## Global App Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        TEACHEROS PHILIPPINES                         │
│                  AI Operating System for DepEd Teachers              │
└──────────────────────────────────────────────────────────────────────┘

                              ┌──────────────┐
                              │   LOGIN      │
                              │  /login      │
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                              │  ONBOARDING  │
                              │  /onboarding │
                              │  (wizard)    │
                              └──────┬───────┘
                                     │
                              ┌──────▼───────┐
                    ┌─────────┤  DASHBOARD  ├─────────┐
                    │         │  / (home)   │         │
                    │         └─────────────┘         │
                    │                                 │
         ┌──────────┴──────────┐           ┌─────────┴──────────┐
         │  PRIMARY WORKFLOWS  │           │  SUPPORT SYSTEMS   │
         │  (Left Sidebar)     │           │                    │
         ├─────────────────────┤           ├────────────────────┤
         │ Teaching /teaching  │           │ AI Agents /agents  │
         │ Lesson Plan /lp     │           │ Settings /settings │
         │ Grading /grading    │           └────────────────────┘
         │ Forms /forms        │
         │ Students /students  │         ┌─────────────────────┐
         │ Parents /parents    │         │ AI ASSISTANT SIDEBAR│
         │ Reports /reports    │         │ (global, toggleable)│
         │ Programs /programs  │         └─────────────────────┘
         └─────────────────────┘
```

## Navigation Hierarchy

### Level 0: Authentication
```
Login Screen (/login)
├── Role Selection (Teacher / Adviser / Coordinator)
├── Grade Level Selection
└── Subject Assignment

Onboarding Wizard (/onboarding)
├── Step 1: School Information
├── Step 2: Sections/Classes Setup
├── Step 3: Subject Assignments
└── Step 4: Quick Start Tour
```

### Level 1: Main Dashboard (/)
```
Dashboard (Teacher Home)
├── Today's Classes Timeline
├── Pending Tasks Panel
├── AI Daily Briefing Card
│   └── → Opens AI Assistant sidebar
├── Performance Trend Chart
├── At-Risk Students Panel
│   └── → Click opens Student Hub
└── Quick Action Buttons
    ├── Start Lesson Planning → /lesson-planning
    ├── Start Grading Cycle → /grading
    ├── Generate School Forms → /forms
    └── Ask AI Assistant → Toggles sidebar
```

### Level 2: Workflow Pages (7 Main Workflows)

#### Teaching Workflow (/teaching)
```
Weekly Plan View
├── Day-by-day schedule
├── Lesson completion status
├── Attendance snapshot
└── Formative pulse indicators
    │
    └── Daily Execution View
        ├── Current class card
        ├── Start lesson button
        ├── Attendance quick-capture
        └── Reflection prompt
```

#### Lesson Planning (/lesson-planning)
```
Workflow: Input → AI Generation → Review Editor → Export → Archive
├── Step 1: Input
│   ├── Grade/Subject/Quarter selectors
│   └── MELC Competency Tree
├── Step 2: AI Generation
│   ├── Loading/animation state
│   └── Generated DLL Preview (split view)
├── Step 3: Review Editor
│   ├── Rich text sections
│   └── AI Suggestions panel
├── Step 4: Export
│   ├── PDF/Word buttons
│   └── Weekly batch option
└── Step 5: Archive
    └── Version history list
```

#### Grading Cycle (/grading)
```
Workflow: Data Input → Weight Config → AI Compute → Analytics → Approval → Export
├── Step 1: Spreadsheet Grid
│   ├── Student rows
│   ├── Written Works columns
│   ├── Performance Tasks columns
│   └── Exam column
├── Step 2: Weight Configuration
│   ├── DepEd pre-sets
│   └── Custom override
├── Step 3: AI Computation
│   ├── Auto-calculate button
│   └── Error detection panel
├── Step 4: Analytics
│   ├── Class performance chart
│   ├── At-risk list
│   └── Ranking table
├── Step 5: Approval
│   ├── Draft/Review/Finalize toggle
│   └── Sign-off log
└── Step 6: Export
    └── Grade sheets / SF9 export
```

#### School Forms (/forms)
```
Workflow: Select Form → Data Source → Validation → Auto-Fill → Preview → Correct → Export
├── Form Selector Cards
│   ├── SF1 (School Register)
│   ├── SF2 (Daily Attendance)
│   ├── SF5 (Promotion Report)
│   ├── SF9 (Progress Report)
│   └── SF10 (Permanent Record)
├── Data Source Upload
│   ├── Excel Upload
│   ├── LIS Import
│   └── Manual Input
├── Validation Dashboard
│   ├── Missing students highlight
│   ├── Errors in red
│   └── AI fix suggestions
├── AI Auto-Fill Preview
│   ├── Exact DepEd layout
│   └── Editable fields
└── Export & Submission Tracker
    ├── PDF/Excel export
    └── Status: Not Started → In Progress → Submitted → Approved
```

#### Student Hub (/students)
```
Student List View
├── Search bar
├── Filters (At-risk / High achievers / Attendance issues)
└── Student cards
    │
    └── Student Profile (click)
        ├── Timeline: Grades, Attendance, Notes
        ├── Risk Score Indicator
        └── Intervention Suggestions
            │
            └── Case Management
                ├── Issue → Action → Outcome
                └── Review schedule
```

#### Parent Communication (/parents)
```
Workflow: Select Student → Select Issue → AI Draft → Preview → Send → History
├── Student Selector
├── Issue Type (Absence / Grade / Behavior / Achievement)
├── AI Message Generator
│   ├── Tagalog/English toggle
│   └── Tone selector
├── Preview Screen
│   ├── SMS preview
│   └── Messenger preview
└── Communication History
    └── Log per student with timeline
```

#### Reports & Compliance (/reports)
```
Workflow: Template → AI Draft → Review → Attach Evidence → Export → Submit
├── Report Templates
│   ├── RPMS
│   ├── Monthly Accomplishment
│   └── Narrative Reports
├── AI Report Builder
│   ├── Input form
│   └── Generated draft preview
├── Evidence Upload
│   ├── Drag-and-drop
│   └── Auto-linked assets
└── Export & Submission Tracking
    ├── PDF download
    └── Approval chain tracker
```

#### School Programs (/programs)
```
Program Dashboard
├── Program Cards
│   ├── Feeding Program
│   ├── DRRM
│   └── Brigada Eskwela
└── Status indicators
    │
    └── Selected Program
        ├── Planning Phase (Gantt timeline)
        ├── Budget Input
        ├── Execution Log
        └── AI Post-Activity Report
```

### Level 3: Global Systems

#### AI Agent Workspace (/agents)
```
Multi-agent dashboard
├── Agent Selection Sidebar
│   ├── Lesson Planning Agent
│   ├── Assessment Agent
│   ├── Grade Computation Agent
│   ├── Forms Agent
│   ├── Report Writing Agent
│   └── Student Risk Analyst
├── Agent Workspace (main)
│   ├── Task input
│   ├── Memory context
│   └── Execution log
└── Recent runs history
```

#### AI Assistant Sidebar (Global)
```
Persistent toggle-able panel on ALL pages
├── Context-aware chat input
├── "Use this screen data" toggle
├── Quick actions
│   ├── Fix errors
│   ├── Generate report
│   └── Summarize page
└── Memory panel (recent actions)
```

## Navigation Components

### Desktop (≥1024px)
```
┌──────────────┬─────────────────────────────────────────────────────┐
│   SIDEBAR    │                   MAIN CONTENT                      │
│   (Wide)     │                                                     │
│              │  ┌──────────────────────────────────────────────┐   │
│  Logo        │  │  Top Bar: Search | Notifications | Profile  │   │
│              │  ├──────────────────────────────────────────────┤   │
│  Home        │  │                                              │   │
│  Teaching ──►│  │         PAGE CONTENT                         │   │
│  Lesson ──►  │  │         (Workflow Stepper)                   │   │
│  Grading ──► │  │                                              │   │
│  Forms ──►   │  └──────────────────────────────────────────────┘   │
│  Students ──►│                                                     │
│  Parents ──► │        [AI Assistant toggle button → sidebar]       │
│  Reports ──► │                                                     │
│  Programs ──►│                                                     │
│              │                                                     │
│  AI Agents   │                                                     │
│  Settings    │                                                     │
│              │                                                     │
│ [AI Status]  │                                                     │
└──────────────┴─────────────────────────────────────────────────────┘
```

### Tablet (768–1023px)
```
┌──────────┬───────────────────────────────────────────────────────┐
│ Collapsed│                   MAIN CONTENT                        │
│ Sidebar  │                                                       │
│ (Icons)  │  Top Bar: Menu | Search | Notif | Profile            │
│          ├───────────────────────────────────────────────────────┤
│ 🏠       │                                                       │
│ 📅 ───►  │         PAGE CONTENT                                  │
│ 📘 ──►   │         (Same, but narrower)                         │
│ 🧮 ──►   │                                                       │
│ 📄 ──►   │                                                       │
│ 👥 ──►   │                                                       │
│ 💬 ──►   │                                                       │
│ 📊 ──►   │                                                       │
│ 🏫 ──►   │                                                       │
│          │                                                       │
│ 🤖       │                                                       │
│ ⚙️       │                                                       │
└──────────┴───────────────────────────────────────────────────────┘
```

### Mobile (<768px)
```
┌─────────────────────────────────────┐
│         TOP BAR                     │
│  Logo | Search | Notifications     │
├─────────────────────────────────────┤
│                                     │
│         PAGE CONTENT                │
│         (Stacked layout)           │
│                                     │
├─────────────────────────────────────┤
│   BOTTOM NAVIGATION (5 tabs)        │
│ 🏠  📘  🧮  📄  🤖                 │
│ Home LP  Grad Forms AI              │
└─────────────────────────────────────┘
```

## Workflow State Transitions

```
Every workflow follows:
INPUT → AI PROCESSING → REVIEW → EDIT → EXPORT → TRACK SUBMISSION

    ┌───────┐    ┌──────────┐    ┌────────┐    ┌──────┐    ┌────────┐    ┌────────────────┐
    │ INPUT │───▶│ AI PRO-  │───▶│ REVIEW │───▶│ EDIT │───▶│EXPORT  │───▶│ SUBMISSION    │
    │       │    │ CESSING  │    │        │    │      │    │        │    │ TRACKER       │
    └───────┘    └──────────┘    └────────┘    └──────┘    └────────┘    └────────────────┘
       │             │              │            │            │                │
       │ Auto-       │ Progress     │ AI         │ Auto-      │ Download       │ Status:       │
       │ save        │ indicator    │ suggestions│ save       │ PDF/Word       │ Not Started   │
       │             │ Loading      │            │ Inline     │ Print          │ In Progress   │
       │             │ state        │            │ improve    │                │ Submitted     │
       │             │              │            │ button     │                │ Approved      │
       └─────────────┴──────────────┴────────────┴────────────┴────────────────┴────────────────┘

Each step MUST show:
- Status (done/active/pending)
- Progress bar
- "Next Step" button
- AI assistance available