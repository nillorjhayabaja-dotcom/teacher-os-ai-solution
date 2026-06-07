# TeacherOS — Responsive Variants

## Breakpoint Grid

```
┌──────────┬───────────┬──────────────┬────────────┬──────────────┐
│ Variant  │ Width     │ Sidebar      │ Columns    │ Font Scale   │
├──────────┼───────────┼──────────────┼────────────┼──────────────┤
│ Mobile   │ < 768px   │ Hidden       │ 1 column   │ 14px body    │
│ Tablet   │ 768-1023  │ Icons only   │ 2 columns  │ 14px body    │
│ Desktop  │ 1024-1439 │ Full (240px) │ 3 columns  │ 14px body    │
│ Wide     │ ≥ 1440    │ Full (280px) │ 4 columns  │ 15px body    │
└──────────┴───────────┴──────────────┴────────────┴──────────────┘
```

---

## A. Desktop Layout (≥1024px) — Reference

```
┌──────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────┬────────────────────────────────────────────┐   │
│  │                 │  [🔍 Search...]          [🔔] [👤 MR]    │   │
│  │   SIDEBAR      ├────────────────────────────────────────────┤   │
│  │   (240px)      │                                              │   │
│  │                 │  PAGE CONTENT                                 │   │
│  │  🧠 TeacherOS  │  max-width: 1600px, centered                │   │
│  │                 │                                              │   │
│  │  🏠 Dashboard   │  ┌──────────┬──────────┐  ┌──────────────┐ │   │
│  │  📅 Teaching    │  │ Card 1/2 │ Card 2/2│  │ AI Sidebar   │ │   │
│  │  📘 Lesson      │  ├──────────┼──────────┤  │ (optional,   │ │   │
│  │  🧮 Grading     │  │ Card 1/3 │ Card 2/3│  │  320px)      │ │   │
│  │  📄 Forms       │  │ Card 3/3 │          │  │              │ │   │
│  │  👥 Students    │  └──────────┴──────────┘  │              │ │   │
│  │  💬 Parents     │                           │              │ │   │
│  │  📊 Reports     │  [← Back]  [Continue →]  │              │ │   │
│  │  🏫 Programs    │                           │              │ │   │
│  │                 │                           │              │ │   │
│  │  🤖 AI Agents   │  ✓ Autosaved 10:30 AM    │              │ │   │
│  │  ⚙️ Settings    │                           │              │ │   │
│  │                 └───────────────────────────┴──────────────┘ │   │
│  │  🤖 AI Active   │                                              │   │
│  └─────────────────┴──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## B. Tablet Layout (768–1023px)

```
┌──────────┬──────────────────────────────────────────────────────────┐
│ [≡]      │  Search...                     [🔔] [👤]               │
│ Icons    ├──────────────────────────────────────────────────────────┤
│          │                                                          │
│ 🏠       │  PAGE CONTENT — 2 columns                                │
│ 📅       │                                                          │
│ 📘    ▶ │  ┌─────────────────┐  ┌─────────────────┐               │
│ 🧮       │  │ Workflow        │  │ AI Tips          │               │
│ 📄       │  │ Input card      │  │ or secondary     │               │
│ 👥       │  │                 │  │ panel            │               │
│ 💬       │  └─────────────────┘  └─────────────────┘               │
│ 📊       │                                                          │
│ 🏫       │  ┌──────────────────────────────────────────────────┐   │
│          │  │ Full-width content (tables, forms, previews)     │   │
│ 🤖       │  └──────────────────────────────────────────────────┘   │
│ ⚙️       │                                                          │
│          │  [← Back]  [Continue →]                                 │
│          └──────────────────────────────────────────────────────────┘

Key Differences from Desktop:
├── Sidebar: 64px wide, icons only (no labels)
├── Labels appear as tooltips on hover
├── Hamburger menu to expand sidebar temporarily
├── Content: 2-column grid max (instead of 3)
├── AI sidebar: 280px wide (instead of 320px)
├── Tables: horizontal scroll with sticky first column
├── Padding: 16px (instead of 24px)
└── Stepper: compact, text truncated, scrollable
```

---

## C. Mobile Layout (<768px)

```
┌─────────────────────────────────────┐
│  Back     Lesson Planning    💾  ⋮  │
├─────────────────────────────────────┤
│                                     │
│  Step 1 of 5: Input                 │
│  ████████░░░░░░░░░░ 40%            │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Grade Level   [6 ▾]        │   │
│  ├─────────────────────────────┤   │
│  │ Subject       [Math ▾]     │   │
│  ├─────────────────────────────┤   │
│  │ Quarter       [Q1 ▾]       │   │
│  └─────────────────────────────┘   │
│                                     │
│  MELC Competencies                  │
│  ┌─────────────────────────────┐   │
│  │ ✓ M6NS-Ia-86 Add/Sub frac │   │
│  │ ○ M6NS-Ib-87 Problem solv │   │
│  │ ✓ M6NS-Ic-90 Multiply fra │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │      Continue →            │   │
│  └─────────────────────────────┘   │
│                                     │
├─────────────────────────────────────┤
│ 🏠  📘LP  🧮Grad  📄Forms  🤖AI   │
│                   ● active         │
└─────────────────────────────────────┘

Key Differences from Desktop:
├── Sidebar: completely hidden
├── Bottom Navigation Bar: 5 primary tabs
│   ├── 🏠 Home (Dashboard)
│   ├── 📘 Lesson Planning
│   ├── 🧮 Grading Cycle
│   ├── 📄 School Forms
│   └── 🤖 AI Assistant
├── Top Bar: collapsed — just back button + title + actions
├── Content: single column, full width
├── Cards: full width, no grid
├── Tables: horizontal scrollable, sticky first column
├── Stepper: horizontal scroll snap, compact
├── Dropdowns: full-width, select native
├── Buttons: full-width on primary actions
├── AI sidebar: full-screen overlay when opened
├── Dialog/modals: full-screen when appropriate
├── Touch targets: minimum 44px
├── Font: same size, no scaling down
├── Padding: 16px horizontal, 12px vertical
└── Safe area: bottom nav accounts for notches
```

---

## D. Component Responsive Behaviors

### D1. Navigation

```
Sidebar
├── Desktop:   240px fixed, full labels, AI status bar at bottom
├── Tablet:    64px icons, labels on hover tooltip
└── Mobile:    hidden, replaced by bottom nav

Top Bar
├── Desktop:   56px, search visible, notification + profile
├── Tablet:    56px, search compact, profile name hidden
└── Mobile:    48px, no search (moved to content), hamburger

Bottom Nav (Mobile Only)
├── Height:    64px (56px bar + 8px safe area)
├── Items:     5 max, spaced evenly
├── Icons:     24px
├── Labels:    10px semibold
└── Active:    primary tint + dot indicator
```

### D2. Workflow Stepper

```
Desktop
├── Horizontal row: all steps visible
├── Each: 180px min-width
├── Circle: 24px, number or check
├── Title: 14px
└── Desc: 12px below

Tablet
├── Horizontal with overflow-x scroll
├── Snap scroll per step
├── Compact: circle only, title truncated
└── Desc: hidden

Mobile
├── Horizontal scroll snap
├── Compact: circle + short title
├── Progress bar above
└── Current step highlighted
```

### D3. Data Tables

```
Desktop
├── Full table visible (up to 8 columns)
├── 48px row height
├── Horizontal overflow on wide tables
└── Sticky first column (name)

Tablet
├── Up to 6 columns visible
├── Horizontal scroll with sticky name column
├── 44px row height (smaller touch target)
└── Alternating row colors

Mobile
├── Up to 4 columns visible
├── Horizontal scroll with sticky name column
├── 44px row height
├── Compressed: "WW" instead of "Written Works"
└── Swipe to reveal actions
```

### D4. Forms & Inputs

```
Desktop
├── Inputs: 40px height, max-width 400px
├── Inline: label left, input right
├── Buttons: inline with text
└── Multi-select: searchable dropdown

Tablet
├── Inputs: 40px height, full-width on mobile context
├── Stack: label above input
├── Buttons: full-width primary, inline secondary
└── Multi-select: scrollable list

Mobile
├── Inputs: 44px height (touch-friendly), full-width
├── Stack: label above input
├── Select: native picker
├── Buttons: full-width primary
└── All inputs: auto-capitalize off for LRN fields
```

### D5. AI Sidebar

```
Desktop
├── Width: 320px
├── Position: fixed right below top bar
├── Animation: slide-in from right (200ms)
├── Overlay: no, pushes content (or overlaps with bg dim)
└── Toggle: button in top bar

Tablet
├── Width: 280px
├── Position: same as desktop
├── Overlay: semi-transparent backdrop
└── Toggle: icon button

Mobile
├── Width: 100vw (full screen)
├── Position: full overlay
├── Header: close button + title
├── Content: scrollable
├── Input: fixed at bottom (keyboard-aware)
└── Backdrop: semi-transparent black
```

### D6. Dashboard Components

```
Quick Action Cards
├── Desktop: 4-column grid
├── Tablet: 2-column grid
└── Mobile: 2-column grid, smaller cards

Today's Schedule
├── Desktop: list with time, subject, section, badge
├── Tablet: same but narrower
└── Mobile: compact list, time + subject only

Pending Workflows
├── Desktop: full list with severity dots and Resume button
├── Tablet: same but no module label
└── Mobile: truncated list, swipe to mark complete

At-Risk Students
├── Desktop: 3-column grid of cards
├── Tablet: 2-column grid
└── Mobile: horizontal scroll cards
```

### D7. Gantt Chart (Programs)

```
Desktop
├── Full timeline: 8-10 weeks visible
├── 48px row height
├── Task name + bar
└── Legend visible

Tablet
├── 6-8 weeks visible
├── Horizontal scroll for more
├── 44px row height
└── Compact task names

Mobile
├── 4 weeks visible
├── Horizontal scroll
├── 40px row height
└── Swipeable timeline
```

### D8. Grading Spreadsheet

```
Desktop
├── All columns: Student, WW1-2, PT1-2, Exam, Final
├── Editable: click cell to edit
├── Summary row at bottom
└── Horizontal scroll if >8 columns

Tablet
├── 6 columns visible at a time
├── Scroll horizontally for rest
├── Sticky first 2 columns (Student + first score)
└── Editing: tap cell, modal editor

Mobile
├── 4 columns visible
├── Scroll horizontally
├── Sticky: Student column + Final grade
├── Editing: tap opens full-screen row editor
└── Summary: collapsible footer
```

---

## E. AI Sidebar — Responsive Breakpoints

```
┌────────┬────────┬──────────┬────────────┬──────────────┐
│ State  │ Device │ Width    │ Backdrop   │ Behavior     │
├────────┼────────┼──────────┼────────────┼──────────────┤
│ Open   │ Desktop│ 320px    │ None       │ Pushes main │
│ Open   │ Tablet │ 280px    │ Dim (0.3)  │ Overlays    │
│ Open   │ Mobile │ 100vw    │ Dim (0.5)  │ Full screen  │
│ Closed │ All    │ 0px      │ None       │ Hidden       │
└────────┴────────┴──────────┴────────────┴──────────────┘
```

---

## F. Layout Transition Rules

```
When resizing from Desktop → Tablet:
├── Sidebar: 240px → 64px (icons only)
├── Grid: 3-col → 2-col
├── AI sidebar: pushes → overlays
├── Top bar: profile name hidden
└── Padding: 24px → 16px

When resizing from Tablet → Mobile:
├── Sidebar: hidden
├── Bottom nav: appears
├── Grid: 2-col → 1-col
├── AI sidebar: -> full screen overlay
├── Top bar: compact (back + title only)
├── Dropdowns: -> native pickers
├── Buttons: -> full-width
└── Touch targets: -> 44px minimum
```

---

## G. Mobile-Specific UX Patterns

```
Pull-to-Refresh
├── Dashboard: refresh pending tasks
├── Students: refresh student list
└── Forms: revalidate data

Swipe Gestures
├── Student list: swipe left → reveal actions
├── Workflow steps: swipe to go next/prev
├── Notifications: swipe to dismiss
└── Sidebar: swipe to close

Bottom Sheet
├── Student quick-view from list
├── Grade cell editor (tap cell)
├── AI suggestion detail
└── Filter selection

Offline Indicator
├── Banner at top: "You're offline — changes will sync when connected"
├── Buttons disabled: AI features
├── Cache indicator: "Cached data (last synced 2h ago)"
└── Queue counter: "3 changes pending sync"