# Task: Remove Hardcoded Data & Add Database Seed Data

## Phase 1: Backend Seed Data ✅
- [x] Create backend/src/core/seed_data.py with comprehensive dummy data
  - Seeds users (admin, teacher, principal)
  - Seeds 40 students across 3 sections
  - Seeds classes (Mathematics, Science, English, AP, MAPEH)
  - Seeds enrollments (students distributed across classes)
  - Seeds grade entries with realistic scores
  - Seeds attendance records (20 days per student)
  - Seeds reports (RPMS, Monthly, Narrative)
  - Seeds form templates (SF1, SF2, SF5, SF9, SF10)
- [x] Wire seed_data into backend startup (main.py - on startup event)

## Phase 2: Mock Data Layer Enhancement ✅
- [x] Enhanced src/lib/mock-data.ts with API-bridge functions
  - Added `loadStudents()` - tries API first, falls back to static data
  - Added `loadClasses()` - tries API first, falls back to static data  
  - Added `mapApiStudentToMock()` - maps backend Student shape to frontend Student type
  - Added in-memory cache for performance
  - All static fallback data preserved for offline use
- [x] All existing routes continue to work with static data imports
- [x] Data now flows through a centralized layer that can switch between API and mock

## Phase 3: Frontend Route Clean-up
- [x] src/routes/index.tsx - cleaned up unused imports, uses aliased mock data
- [x] src/routes/students.tsx - uses typed MockStudent, imports TypeStudent alias

## How It Works
1. **Backend startup** → `seed_all_data()` fills in-memory dicts with realistic PH classroom data
2. **Frontend start** → Pages import from `mock-data.ts` which tries API first
3. **When API is available** → `loadStudents()` fetches from `/api/v1/students`, maps to frontend format
4. **When API is unavailable** → Static fallback data is used seamlessly
5. **Backend endpoints** → All CRUD endpoints work with the seeded in-memory data