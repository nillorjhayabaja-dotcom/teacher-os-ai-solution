# TeacherOS — Component System & Design Tokens

## 1. Color Tokens

```
Primary Colors
├── Primary:      #2563eb (oklch 0.55 0.20 258)   — Buttons, links, active states, icons
├── Primary Soft: #eef2ff (oklch 0.96 0.025 258) — Card backgrounds, active rows
├── Primary Dark: #1d4ed8                        — Hover states, pressed buttons
└── Primary Light: #dbeafe                       — Light accents

Status Colors
├── Success:   #16a34a  — Completed, synced, healthy, active
├── Warning:   #d97706  — In-progress, attention needed, medium risk
├── Destructive: #dc2626 — Errors, at-risk students, overdue, critical
├── Info:      #2563eb  — Informational, AI suggestions, new items
└── Muted:     #64748b  — Secondary text, disabled, metadata

Neutrals
├── Background: #ffffff / #f8fafc
├── Foreground: #0f172a (oklch 0.18 0.03 260)
├── Card:       #ffffff
├── Border:     #e2e8f0 (oklch 0.92 0.008 255)
├── Input:      #e2e8f0
├── Sidebar BG: #f8fafc
└── Sidebar BG Dark: #1e293b

Semantic Maps
├── Chart 1: Primary blue
├── Chart 2: Success green
├── Chart 3: Warning amber
├── Chart 4: Purple (#a855f7)
└── Chart 5: Teal (#14b8a6)
```

## 2. Typography Scale

```
Headings (Plus Jakarta Sans)
├── H1: 36px / 2.25rem — Page title (Dashboard greeting)
├── H2: 30px / 1.875rem — Section titles
├── H3: 24px / 1.5rem — Card headers
├── H4: 20px / 1.25rem — Panel titles
└── H5: 18px / 1.125rem — Sub-panel headers

Body (Inter)
├── Large:   16px / 1rem — Body text, descriptions
├── Regular: 14px / 0.875rem — Content, table cells
├── Small:   13px / 0.8125rem — Metadata, labels
├── XSmall:  12px / 0.75rem — Footnotes, timestamps
└── Tiny:    11px / 0.6875rem — Badges, legal

Monospace
├── LRN:     11px font-mono — Student LRN display
├── Code:    12px font-mono — MELC codes
└── Time:    11px font-mono — Schedule times

Line Heights
├── Tight:   1.2 — Headings
├── Normal:  1.5 — Body
└── Relaxed: 1.75 — Long text (forms, letters)

Font Weights
├── Regular:  400
├── Medium:   500
├── Semibold: 600
└── Bold:     700
```

## 3. Spacing System (8px grid)

```
├── 1:  4px (0.25rem)   — Stack gutters, gap between icon & text
├── 2:  8px (0.5rem)    — Inner padding small
├── 3:  12px (0.75rem)  — Inner padding default
├── 4:  16px (1rem)     — Card padding, grid gap
├── 5:  20px (1.25rem)  — Section spacing
├── 6:  24px (1.5rem)   — Between workflow steps
├── 8:  32px (2rem)     — Page section spacing
├── 10: 40px (2.5rem)   — Between major sections
├── 12: 48px (3rem)     — Page padding
└── 16: 64px (4rem)     — Hero spacing
```

## 4. Border Radius

```
├── Default:  0.75rem (12px)  — Cards, containers
├── Small:    0.5rem (8px)   — Buttons, inputs, badges
├── Medium:   0.625rem (10px) — Tooltips, popovers
├── Large:    1rem (16px)    — Modals, dialogs
├── Full:     9999px         — Avatars, pills
```

## 5. Shadows

```
├── Elegant:  0 1px 2px 0 rgba(0,0,0,0.04), 0 8px 24px -8px rgba(0,0,0,0.10)
├── Glow:     0 0 0 1px rgba(37,99,235,0.08), 0 12px 40px -12px rgba(37,99,235,0.35)
├── Card:     var(--shadow-elegant) — Default card shadow
├── Dropdown: 0 4px 16px rgba(0,0,0,0.08) — Menus, selects
├── Modal:    0 20px 60px rgba(0,0,0,0.15) — Dialog backdrop
└── Hover:    0 8px 30px rgba(0,0,0,0.06) — Card hover state
```

## 6. Component Library

### 6.1 Button System

```
Primary Button
├── Height: 40px (default), 32px (small), 48px (large)
├── Padding: 12px 20px (default), 8px 12px (small), 16px 24px (large)
├── Background: var(--primary)
├── Color: white
├── Border: none
├── Radius: 0.5rem
├── Font: 14px semibold
└── States: hover (darken), active (press), disabled (opacity 50%)

Secondary/Outline Button
├── Same dimensions as primary
├── Background: transparent
├── Border: 1px var(--border)
├── Color: var(--foreground)
└── Hover: bg var(--accent)

Ghost Button
├── Same dimensions
├── Background: transparent
├── No border
├── Color: var(--muted-foreground)
└── Hover: bg var(--muted)

Icon Button
├── Size: 36px x 36px
├── Icon: 16px
├── Rounded: 0.5rem
└── Variants: ghost, outline, solid
```

### 6.2 Card System

```
Default Card
├── Background: var(--card) / white
├── Border: 1px var(--border)
├── Radius: 0.75rem
├── Shadow: var(--shadow-elegant)
├── Padding: 20px (default), 24px (large), 16px (compact)
└── Hover: border-primary, shadow-elevated

Interactive Card (clickable)
├── All default card styles
├── Cursor: pointer
├── Hover: lift (translateY -1px)
└── Active: scale(0.99)

Stat Card
├── Height: 80px
├── Layout: label top, value bottom-left
├── Value: 32px display font
└── Trend: inline icon (up/down/flat)

Metric Card
├── Height: 100px
├── Layout: label top, value + trend inline
├── Value: 24px display font
└── Trend: color-coded (green/red/neutral)
```

### 6.3 Table/Grid System

```
Data Table
├── Header: uppercase 10px, semibold, muted-foreground
├── Row height: 48px
├── Cell padding: 12px 16px
├── Border: bottom border per row
├── Background: alternating white/transparent
└── Hover: bg var(--muted)/40

Spreadsheet Grid
├── Header: sticky, uppercase 10px, border-bottom
├── Cell: 40px height, border, editable on click
├── Sticky columns: first column (name) always visible
├── Horizontal scroll for many columns
├── Error cell: red bg tint
└── Final grade: bold, <75 warning icon

Student List
├── Avatar: 36px circle, initials, color-coded by risk
├── Name: 14px semibold
├── Subtitle: 11px muted (section, LRN)
├── Right: grade + attendance
└── Filter bar: tabs for All/At-Risk/Achievers
```

### 6.4 Workflow Stepper

```
Horizontal Stepper
├── Height: 72px
├── Items: 5-6 steps in a row
├── Each item: number circle (24px) + title + description
├── Active: primary border, primary-soft bg
├── Completed: success border, check icon
├── Pending: border border, muted
└── Clickable: navigate to any completed or current step

Progress Bar
├── Height: 4px
├── Track: var(--muted)
├── Fill: var(--primary) or var(--success) for complete
└── Animated: smooth transition on step change
```

### 6.5 Form Controls

```
Text Input
├── Height: 40px
├── Padding: 10px 12px
├── Border: 1px var(--input)
├── Radius: 0.5rem
├── Background: var(--background)
├── Font: 14px
└── Focus: ring 2px var(--ring)/30

Select Dropdown
├── Same as text input
├── Chevron icon on right
└── Native or custom dropdown

Checkbox/Toggle
├── Checkbox: 16px square, rounded 4px
├── Toggle: 36px wide, 20px high
├── Active: primary bg
└── Disabled: opacity 50%

Radio Card
├── 160px x 120px
├── Icon + label + description
├── Border: 1px var(--border)
├── Selected: primary border + primary-soft bg
└── Hover: primary border

Tag/Pill
├── Height: 24px
├── Padding: 4px 8px
├── Radius: 999px
├── Font: 10px semibold
└── Colors: primary, success, warning, destructive
```

### 6.6 AI-Related Components

```
AI Suggestion Card
├── Background: primary-soft (var(--primary-soft))
├── Border-left: 4px var(--primary)
├── Padding: 16px
├── Icon: Sparkles (16px, primary)
├── Text: 13px
└── Action button: small, primary outline

AI Briefing Card
├── Gradient border: primary/30
├── Background: gradient primary-soft → card
├── Icon: 32px gradient circle
├── Items: flex row, icon + text
└── CTA: primary link at bottom

Memory Panel (AI sidebar)
├── Item: 32px height
├── Icon: check (done), circle (pending)
├── Color: success (done), muted (pending)
└── Click: re-run action

Execution Log (AI Agents)
├── Monospace font: 12px
├── Line height: 1.6
├── Colors: success (✓), primary (✨), muted (⏳)
└── Animation: sequential reveal
```

### 6.7 Navigation Components

```
Sidebar Item
├── Height: 40px
├── Padding: 8px 12px
├── Icon: 16px, primary when active
├── Label: 14px
├── Active: sidebar-accent bg, font-medium
├── Inactive: 80% opacity, hover bg
└── Badge: 10px pill, primary/10 bg

Top Bar
├── Height: 56px
├── Border-bottom: 1px var(--border)
├── Background: bg-background/80 + backdrop-blur
├── Search: 36px height, 400px max-width
├── Notification bell: 36px ghost button
└── Profile: 32px avatar + name + section

Mobile Bottom Nav
├── Height: 64px (+ safe area)
├── Background: white, border-top
├── Items: 5 tabs
├── Each: icon (24px) + label (10px)
├── Active: primary icon + dot
└── Inactive: muted-foreground
```

### 6.8 Data Visualization

```
Chart Wrapper
├── Height: 200px (small), 300px (medium), 400px (large)
├── Responsive width
├── Background: transparent
└── Tooltip: popover style, 12px text

Class Performance Area Chart
├── X-axis: weeks
├── Y-axis: hidden or narrow
├── Gradient fill: primary blue
├── Line: 2px primary stroke
└── Grid: dashed, muted

Gantt Chart (Programs)
├── Row: 48px
├── Task name: left column
├── Bar: 20px height, rounded
├── Colors: blue (done), yellow (in-progress), dashed (pending)
└── Week columns: 100px each
```

## 7. Animation & Motion

```
Transitions
├── Default: 200ms ease
├── Slow: 300ms ease
├── Fast: 150ms ease
└── Bounce: 300ms cubic-bezier(0.34, 1.56, 0.64, 1)

Key Animations
├── Pulse: opacity change for loading states
├── Slide-in: sidebar enters from right
├── Fade-in: content appears
├── Progress: gradient shift for indeterminate bars
└── Scale: card hover (1.02)

State Indicators
├── Online: pulsing green dot (1.5px)
├── Loading: spinning ring or gradient progress
├── Success: checkmark scale-in
└── Error: shake animation (rare, for forms only)
```

## 8. Responsive Breakpoints

```
├── Mobile:  < 768px  — Single column, bottom nav, no sidebar
├── Tablet:  768-1023px — Collapsed sidebar (icons only), 2-column grid
├── Desktop: 1024-1439px — Full sidebar, 3-column grid max
└── Wide:    ≥ 1440px  — Full layout, 4-column grid, max-width 1600px
```

## 9. DepEd-Specific Patterns

```
DepEd Form Display
├── Font: serif (Times New Roman / Georgia) for authenticity
├── Borders: 1px solid, black/80
├── Header: centered, Republic → DepEd → Region → School
├── Table: full width, bordered cells
├── Signature lines: name + date blanks
└── Paper: legal size (8.5 x 14 in) aspect ratio

SF Numbering
├── SF1: School Register (class list)
├── SF2: Daily Attendance Report
├── SF3: Books Issued & Returned
├── SF4: Disposal Record
├── SF5: Report on Promotion / Level of Proficiency
├── SF6: Kinder Progress Report
├── SF7: School Form for Children with Special Needs
├── SF8: Learner's Basic Health Profile
├── SF9: Learner's Progress Report Card
└── SF10: Learner's Permanent Record

MELC Format
├── Code: [Grade][Subject Code]-[Quarter][Competency Number]
├── Example: M6NS-Ia-86
├── M = Mathematics, 6 = Grade, NS = Numbers & Number Sense
├── I = Quarter 1, a = Week 1, 86 = Competency #
└── Display: mono font code + description text
```

## 10. Accessibility Standards

```
├── All interactive elements: focus-visible ring
├── Color contrast: WCAG AA minimum (4.5:1 for text)
├── Labels: all inputs have visible or aria-label
├── Headings: logical hierarchy (h1→h2→h3)
├── Nav: landmark roles, keyboard navigation
├── Tables: scope attributes on headers
├── Buttons: minimum 40px touch target
├── Motion: prefers-reduced-motion respected
└── Screen readers: aria-live for dynamic content