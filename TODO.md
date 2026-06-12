# TODO — Frontend: remove hardcoded dashboard data

- [ ] Replace `src/routes/students.tsx` to fetch students from backend API (no `mockStudents`).
- [ ] Replace `src/routes/index.tsx` dashboard to fetch classes/pending workflows/at-risk/performance from backend API (no mocks).
- [x] Replace dependency on `src/lib/mock-data.ts` in `src/routes/students.tsx`.
- [x] Start removing mock imports from `src/routes/index.tsx` (dashboard now uses query hooks).
- [ ] Finish removing all remaining hardcoded dashboard data in `src/routes/index.tsx`.
- [ ] Refactor `src/lib/mock-data.ts`: keep only optional offline fallback (or remove exports entirely), and ensure no UI uses it for production rendering.
- [ ] Ensure backend demo seed is enabled when running frontend/backend (development/demo env).
- [ ] Run frontend typecheck/build and backend start to verify endpoints return seeded data.

