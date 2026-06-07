# TeacherOS — User Flow Diagrams

## Flow 1: Authentication & Onboarding

```mermaid
flowchart TD
    A[Open TeacherOS] --> B{Has account?}
    B -->|No| C[Sign Up]
    C --> D[Enter DepEd Email]
    D --> E[Verify Email]
    E --> F[Onboarding Wizard Start]
    
    B -->|Yes| G[Login]
    G --> H[Enter Credentials]
    H --> I{Valid?}
    I -->|No| J[Show Error]
    J --> H
    I -->|Yes| K{Dashboard Ready?}
    
    F --> L[Step 1: Select Role]
    L --> M[Step 2: Select Grade Levels]
    M --> N[Step 3: Assign Subjects]
    N --> O[Step 4: Set Up Sections]
    O --> P[Class Setup: Section + Subject + Students]
    P --> Q{Done?}
    Q -->|No| P
    Q -->|Yes| R[Step 5: Quick Start Tour]
    R --> S[Create First DLL or Skip]
    S --> T[Redirect to Dashboard]
    
    K -->|Yes| T
    K -->|No| L
    T --> U[Main Dashboard]
```

## Flow 2: Daily Dashboard → Workflow Launch

```mermaid
flowchart TD
    A[Main Dashboard] --> B{User Action}
    
    B -->|Click class| C[Open Lesson Planning]
    B -->|Click pending task| D[Resume Workflow]
    B -->|Click quick action| E[Launch Workflow Direct]
    B -->|Click AI Briefing| F[Open AI Agent or Sidebar]
    B -->|Click at-risk student| G[Open Student Profile]
    
    C --> H[Lesson Planning Step 1]
    D --> H
    E --> H
    
    H --> I[Select Grade/Subject/MELC]
    I --> J[AI Generate DLL]
    J --> K[Review & Edit DLL]
    K --> L[Export PDF/Word]
    L --> M[Archive Version]
    M --> N[Return to Dashboard]
    
    F --> O[AI Assistant Sidebar Panel]
    O --> P[Ask Question or Run Agent]
    P --> Q[View Results]
    Q --> N
    
    G --> R[Student Intelligence Hub]
    R --> S[View Profile & Risk]
    S --> T[Take Intervention Action]
    T --> N
```

## Flow 3: Complete Grading Cycle (End-to-End)

```mermaid
flowchart TD
    A[Start Grading Cycle] --> B[Step 1: Input Raw Scores]
    B --> C{Data Source?}
    C -->|Excel Upload| D[Parse & Map Columns]
    C -->|Manual Entry| E[Grid Editor]
    C -->|LIS Sync| F[Pull from LIS]
    
    D --> G[Step 2: Configure Weights]
    E --> G
    F --> G
    
    G --> H[Select DepEd Preset or Custom]
    H --> I[Step 3: Run AI Computation]
    
    I --> J{Anomalies?}
    J -->|Yes| K[Error Detection Panel]
    K --> L[Fix: Cap/Flag/Edit]
    L --> M[Recompute]
    M --> J
    
    J -->|No| N[Step 4: View Analytics]
    N --> O[Check Class Performance]
    N --> P[Review At-Risk List]
    N --> Q[View Ranking]
    
    O --> R[Step 5: Approval Workflow]
    P --> R
    Q --> R
    
    R --> S{Draft → Review → Finalize}
    S --> T[Submit for Review]
    T --> U[Head Teacher Reviews]
    U --> V{Approved?}
    V -->|No| W[Revise & Resubmit]
    W --> T
    V -->|Yes| X[Step 6: Export]
    
    X --> Y[Download Grade Sheets]
    X --> Z[Push to SF9]
    X --> AA[Print Report Cards]
    
    Y --> AB[Submission Tracker: Submitted ✓]
    Z --> AB
    AA --> AB
    AB --> AC[Return to Dashboard]
```

## Flow 4: School Forms Pipeline (SF1-SF10)

```mermaid
flowchart TD
    A[Forms Dashboard] --> B[Select Form Type]
    B --> C{SF1/SF2/SF5/SF9/SF10}
    
    C --> D[Step 1: Data Source]
    D --> E{Upload, LIS, Manual?}
    E -->|Excel| F[Upload .xlsx]
    E -->|LIS| G[Connect to LIS API]
    E -->|Manual| H[Type Data]
    
    F --> I[Step 2: Validation]
    G --> I
    H --> I
    
    I --> J[Scan for Errors]
    J --> K{Errors Found?}
    K -->|Yes| L[Show Validation Dashboard]
    L --> M[Review Issues]
    M --> N[Apply AI Fixes]
    N --> O[Re-validate]
    O --> K
    
    K -->|No| P[Step 3: AI Auto-Fill]
    P --> Q[Forms Agent Fills Fields]
    Q --> R[Step 4: Form Preview]
    
    R --> S{DepEd Layout Correct?}
    S -->|No| T[Edit Manually]
    T --> S
    S -->|Yes| U[Step 5: Error Correction Mode]
    
    U --> V[Fix Remaining Red Flags]
    V --> W[Step 6: Export]
    W --> X[Download PDF]
    W --> Y[Download Excel]
    W --> Z[Submit to Principal]
    
    Z --> AA[Submission Tracker]
    AA --> AB[Status: Submitted ✓]
    AB --> AC[Return to Forms Dashboard]
```

## Flow 5: Student Intelligence Hub → Intervention

```mermaid
flowchart TD
    A[Student Hub] --> B[View Student List]
    B --> C{Action}
    
    C -->|Search| D[Type Name]
    D --> E[Filter Results]
    E --> F[Select Student]
    
    C -->|Filter| G[At-Risk / Achievers / Attendance]
    G --> F
    
    F --> H[Student Profile View]
    H --> I[View Metrics: Avg, Att, Notes]
    I --> J[View AI Intervention Suggestions]
    
    J --> K{Take Action}
    K -->|Open Case| L[Case Management Panel]
    K -->|Draft Letter| M[Parent Comms Generator]
    K -->|Schedule| N[Add Remediation Session]
    
    L --> O[Log Issue]
    O --> P[Assign Action]
    P --> Q[Set Outcome Target]
    Q --> R[Schedule Review Date]
    
    M --> S[Select Template]
    S --> T[AI Draft Message]
    T --> U[Edit & Send]
    
    N --> V[Select Date/Time]
    V --> W[Add to Calendar]
    
    R --> X[Return to Profile]
    U --> X
    W --> X
    X --> Y[Status: Intervention Active]
    Y --> Z[Return to Student Hub]
```

## Flow 6: Parent Communication Workflow

```mermaid
flowchart TD
    A[Parent Comms] --> B[Select Student]
    B --> C[Select Issue Type]
    C --> D{Absence / Grade / Behavior / Achievement}
    
    D --> E[AI Message Generator]
    E --> F[Choose Language]
    E --> G[Choose Tone: Formal/Casual]
    
    F --> H[AI Drafts Message]
    G --> H
    
    H --> I[Preview Screen]
    I --> J{Choose Channel}
    
    J -->|SMS| K[Phone Frame Preview]
    J -->|Messenger| L[Chat Preview]
    J -->|Printable| M[Letter Preview]
    
    K --> N{Ready to Send?}
    L --> N
    M --> N
    
    N -->|No| O[Edit Message]
    O --> P[Regenerate or Manual Edit]
    P --> N
    
    N -->|Yes| Q[Send Now or Schedule]
    Q --> R[Send SMS via Gateway]
    Q --> S[Send Messenger via API]
    Q --> T[Download PDF Letter]
    
    R --> U[Log to History]
    S --> U
    T --> U
    
    U --> V[View Communication Timeline]
    V --> W[Student: all comms logged ✓]
    W --> X[Return to Parent Comms Dashboard]
```

## Flow 7: Reports & Compliance Pipeline

```mermaid
flowchart TD
    A[Reports Dashboard] --> B[Select Report Template]
    B --> C{RPMS / Monthly / Narrative}
    
    C --> D[Step 1: Fill Input Form]
    D --> E[Key Accomplishments]
    D --> F[Challenges Faced]
    D --> G[Interventions Applied]
    
    E --> H[Step 2: AI Draft Generation]
    F --> H
    G --> H
    
    H --> I[AI Generates Report Draft]
    I --> J[Step 3: Review & Edit]
    
    J --> K[Edit Sections Inline]
    K --> L{Need More Evidence?}
    
    L -->|Yes| M[Step 4: Evidence Upload]
    M --> N[Drag & Drop Files]
    N --> O[AI Auto-Tags Files]
    O --> L
    
    L -->|No| P[Step 5: Final Review]
    P --> Q[Check Format & Content]
    
    Q --> R{Ready to Export?}
    R -->|No| J
    R -->|Yes| S[Step 6: Export]
    
    S --> T[Download PDF]
    S --> U[Download Word]
    S --> V[Submit to Head Teacher]
    
    V --> W[Submission Tracker]
    W --> X[Draft → Submitted → Approved]
    X --> Y[Return to Reports Dashboard]
```

## Flow 8: School Programs (Feeding/DRRM/Brigada)

```mermaid
flowchart TD
    A[Programs Dashboard] --> B[Select Program]
    B --> C{Feeding / DRRM / Brigada}
    
    C --> D[Program Status Overview]
    D --> E{Current Status}
    
    E -->|Planning| F[Step 1: Program Setup]
    F --> G[Define Objectives]
    G --> H[Set Target Beneficiaries]
    H --> I[Identify Risks]
    
    I --> J[Step 2: Create Timeline]
    J --> K[Gantt Chart Editor]
    K --> L[Add Tasks & Milestones]
    L --> M[Assign Owners & Dates]
    
    M --> N[Step 3: Budget Planning]
    N --> O[Add Line Items]
    O --> P[Auto-Calculate vs MOOE]
    P --> Q[Flag Over/Under Budget]
    
    Q --> R[Step 4: Execution Phase]
    R --> S[Log Daily Activities]
    S --> T[Upload Photos & Headcount]
    T --> U[Track Progress vs Timeline]
    
    U --> V[Step 5: Generate Report]
    V --> W[AI Drafts Post-Activity Report]
    W --> X[Review & Edit]
    X --> Y[Export PDF]
    
    Y --> Z[Mark Program Complete]
    Z --> AA[Return to Programs Dashboard]
```

## Flow 9: Global AI Assistant Interaction

```mermaid
flowchart TD
    A[Any Page in TeacherOS] --> B[Click AI Assistant Icon]
    B --> C[AI Sidebar Opens]
    
    C --> D{User Action}
    
    D -->|Type Question| E[AI Processes Query]
    E --> F[Context-Aware Response]
    F --> G{Follow-up?}
    G -->|Yes| D
    G -->|No| H[Close Sidebar]
    
    D -->|Click Quick Action| I[AI Executes Task]
    I --> J[Fix Errors / Gen Report / Summarize]
    J --> K[Show Results in Sidebar]
    K --> H
    
    D -->|Toggle Context| L[Use Current Page Data]
    L --> M[AI Reads Screen Context]
    M --> D
    
    D -->|View Memory| N[Show Recent AI Actions]
    N --> O[Click Past Action to Re-run]
    O --> D
    
    H --> P[Return to Original Page]
    P --> Q[Autosave AI Session ✓]
```

## Flow 10: Cross-Module Data Movement

```mermaid
flowchart LR
    subgraph "Data Sources"
        A[LIS Database]
        B[Excel Upload]
        C[Manual Input]
    end
    
    subgraph "TeacherOS Core"
        D[Student Records]
        E[Class Schedules]
        F[MELC Competencies]
        G[Grading Weights]
        H[Form Templates]
    end
    
    subgraph "Workflow Outputs"
        I[DLL Files → Print/PDF]
        J[Grade Sheets → SF9]
        K[SF1-SF10 → Division]
        L[Parent Messages → SMS]
        M[Reports → RPMS]
        N[Program Docs → MOOE]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    D --> J
    D --> K
    
    F --> I
    F --> J
    
    G --> J
    
    H --> K
    
    D --> L
    D --> O{At-Risk?}
    O -->|Yes| P[Intervention]
    P --> Q[Parent Contact]
    
    E --> I
    
    D --> M
    M --> R[Evidence Files]
    R --> M
```

## Global Navigation State Machine

```mermaid
stateDiagram-v2
    [*] --> Login
    Login --> Onboarding : First Time
    Login --> Dashboard : Returning User
    
    Onboarding --> Dashboard : Complete
    
    Dashboard --> LessonPlanning : Click LP / Quick Action
    Dashboard --> Grading : Click Grading / Quick Action
    Dashboard --> Forms : Click Forms / Quick Action
    Dashboard --> Students : Click Student / Risk
    Dashboard --> Parents : Click Parent Comms
    Dashboard --> Reports : Click Reports
    Dashboard --> Programs : Click Programs
    Dashboard --> Teaching : Click Teaching
    Dashboard --> Agents : Click AI Briefing
    Dashboard --> Settings : Click Settings
    
    LessonPlanning --> Dashboard : Save & Exit
    Grading --> Dashboard : Complete Cycle
    Forms --> Dashboard : Complete Pipeline
    Students --> Dashboard : Navigate Back
    Parents --> Dashboard : Navigate Back
    Reports --> Dashboard : Complete Submission
    Programs --> Dashboard : Mark Complete
    Teaching --> Dashboard : End Week
    Agents --> Dashboard : Close Workspace
    Settings --> Dashboard : Save Changes
    
    state "AI Assistant Sidebar" as AI {
        [*] --> Chat
        Chat --> QuickAction
        QuickAction --> Chat
        Chat --> Memory
        Memory --> Chat
    }
    
    note right of Dashboard : AI Sidebar accessible\nfrom ALL states
```

## Key Flow Principles

1. **Every workflow follows**: Input → AI Processing → Review → Edit → Export → Track
2. **Undo is always available**: Every step saves automatically
3. **AI is persistent**: The sidebar follows the user across all states
4. **No dead ends**: Every screen has a "Back to Dashboard" path
5. **Progressive disclosure**: Complex workflows reveal steps one at a time