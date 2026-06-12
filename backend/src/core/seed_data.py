"""Seed data for development - populates in-memory stores with realistic data.

On startup, this module is called to fill the in-memory dictionaries
used by each API router so the frontend can demonstrate database-driven
data flow instead of hardcoded mock data.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from uuid import uuid4

# Shared user store
from backend.src.api.v1.auth import _users_db

# Student store
from backend.src.api.v1.students import _students_db

# Grade store
from backend.src.api.v1.grades import _grades_db

# Class stores
from backend.src.api.v1.classes import _classes_db, _enrollments_db

# Attendance store
from backend.src.api.v1.attendance import _attendance_db

# Report store
from backend.src.api.v1.reports import _reports_db

# Form stores
from backend.src.api.v1.forms import _forms_db, _form_instances_db

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

last_names = [
    "Dela Cruz", "Santos", "Reyes", "Bautista", "Gonzales",
    "Ramos", "Aquino", "Mendoza", "Castillo", "Cruz",
    "Villanueva", "Garcia", "Torres", "Flores", "Domingo",
]
first_names_m = [
    "Juan", "Mark", "Carlo", "Joshua", "Angelo",
    "Kim", "Daniel", "Paolo", "Rafael", "Miguel",
]
first_names_f = [
    "Maria", "Andrea", "Jasmine", "Bea", "Althea",
    "Krystel", "Sofia", "Janella", "Camille", "Erika",
]

sections = ["Sampaguita", "Rosal", "Ilang-Ilang"]
subjects = ["Mathematics", "Science", "English", "AP", "MAPEH", "Filipino", "ESP", "TLE"]
guardian_names = [
    "Mrs. Dela Cruz", "Mr. Santos", "Mrs. Reyes",
    "Mr. Bautista", "Mrs. Gonzales",
]


def _generate_lrn(r: random.Random) -> str:
    return f"1370{r.randint(10000000, 99999999)}"


def _generate_contact(r: random.Random) -> str:
    return f"+639{r.randint(100000000, 999999999)}"


# ---------------------------------------------------------------------------
# Public seed function
# ---------------------------------------------------------------------------


def seed_all_data() -> None:
    """Seed all in-memory databases with realistic dummy data."""
    r = random.Random(42)

    # ----- Users -----
    seed_users(r)

    # ----- Students -----
    seed_students(r)

    # ----- Classes -----
    seed_classes(r)

    # ----- Enrollments -----
    seed_enrollments(r)

    # ----- Grades -----
    seed_grades(r)

    # ----- Attendance -----
    seed_attendance(r)

    # ----- Reports -----
    seed_reports(r)

    # ----- Forms -----
    seed_forms(r)

    print("[seed] All seed data loaded successfully.")


def seed_users(r: random.Random) -> None:
    """Seed user accounts."""
    users = [
        {
            "id": "u-admin-001",
            "email": "admin@teacheros.ph",
            "password": "hashed_P@ssw0rd123!",
            "first_name": "Mariel",
            "last_name": "Reyes",
            "role": "super_admin",
            "is_active": True,
            "mfa_enabled": False,
            "organization_id": "org-default-001",
            "school_id": "sch-default-001",
        },
        {
            "id": "u-teacher-001",
            "email": "teacher@teacheros.ph",
            "password": "hashed_Teacher123!",
            "first_name": "Juan",
            "last_name": "Dela Cruz",
            "role": "teacher",
            "is_active": True,
            "mfa_enabled": False,
            "organization_id": "org-default-001",
            "school_id": "sch-default-001",
        },
        {
            "id": "u-principal-001",
            "email": "principal@teacheros.ph",
            "password": "hashed_Principal123!",
            "first_name": "Maria",
            "last_name": "Santos",
            "role": "principal",
            "is_active": True,
            "mfa_enabled": False,
            "organization_id": "org-default-001",
            "school_id": "sch-default-001",
        },
    ]
    for u in users:
        _users_db[u["id"]] = u
    print(f"[seed] {len(users)} users created.")


def seed_students(r: random.Random) -> None:
    """Seed 40 students across 3 sections."""
    students = []
    for i in range(40):
        sex = "M" if r.random() > 0.5 else "F"
        first = r.choice(first_names_m) if sex == "M" else r.choice(first_names_f)
        last = r.choice(last_names)
        attendance = r.randint(70, 100)
        avg_grade = r.randint(72, 97)
        risk = "high" if avg_grade < 78 or attendance < 80 else ("medium" if avg_grade < 85 else "low")
        guardian = r.choice(guardian_names)
        student_id = str(uuid4())
        students.append({
            "id": student_id,
            "first_name": first,
            "last_name": last,
            "middle_name": None,
            "email": None,
            "student_id": _generate_lrn(r),
            "grade_level": "6",
            "section": sections[i % 3],
            "organization_id": "org-default-001",
            "school_id": "sch-default-001",
            "is_active": True,
            "guardian_name": guardian,
            "guardian_contact": _generate_contact(r),
            "address": f"{i+1} Manila St., Bulacan",
        })
    for s in students:
        _students_db[s["id"]] = s
    print(f"[seed] {len(students)} students created.")


def seed_classes(r: random.Random) -> None:
    """Seed classes/sections."""
    classes = [
        {
            "id": "c-math-001",
            "name": "Mathematics 6 - Sampaguita",
            "grade_level": "6",
            "section": "Sampaguita",
            "subject": "Mathematics",
            "teacher_id": "u-teacher-001",
            "teacher_name": "Juan Dela Cruz",
            "school_year": "2026-2027",
            "room": "Rm 201",
            "schedule": "7:30 AM - 8:20 AM MTWHF",
        },
        {
            "id": "c-sci-001",
            "name": "Science 6 - Rosal",
            "grade_level": "6",
            "section": "Rosal",
            "subject": "Science",
            "teacher_id": "u-teacher-001",
            "teacher_name": "Juan Dela Cruz",
            "school_year": "2026-2027",
            "room": "Rm 203",
            "schedule": "8:20 AM - 9:10 AM MTWHF",
        },
        {
            "id": "c-eng-001",
            "name": "English 6 - Ilang-Ilang",
            "grade_level": "6",
            "section": "Ilang-Ilang",
            "subject": "English",
            "teacher_id": "u-teacher-001",
            "teacher_name": "Juan Dela Cruz",
            "school_year": "2026-2027",
            "room": "Rm 205",
            "schedule": "9:30 AM - 10:20 AM MTWHF",
        },
        {
            "id": "c-ap-001",
            "name": "AP 6 - Sampaguita",
            "grade_level": "6",
            "section": "Sampaguita",
            "subject": "AP",
            "teacher_id": "u-teacher-001",
            "teacher_name": "Juan Dela Cruz",
            "school_year": "2026-2027",
            "room": "Rm 201",
            "schedule": "10:20 AM - 11:10 AM MTWHF",
        },
        {
            "id": "c-mapeh-001",
            "name": "MAPEH 6 - Rosal",
            "grade_level": "6",
            "section": "Rosal",
            "subject": "MAPEH",
            "teacher_id": "u-teacher-001",
            "teacher_name": "Juan Dela Cruz",
            "school_year": "2026-2027",
            "room": "Rm 207",
            "schedule": "1:00 PM - 1:50 PM MTWHF",
        },
    ]
    for c in classes:
        _classes_db[c["id"]] = c
    print(f"[seed] {len(classes)} classes created.")


def seed_enrollments(r: random.Random) -> None:
    """Enroll students into classes."""
    student_ids = list(_students_db.keys())
    class_ids = list(_classes_db.keys())
    if not student_ids or not class_ids:
        return
    now = str(datetime.utcnow())
    enrollments = []
    for i, sid in enumerate(student_ids):
        cid = class_ids[i % len(class_ids)]
        student = _students_db[sid]
        enrollments.append({
            "id": str(uuid4()),
            "class_id": cid,
            "student_id": sid,
            "student_name": f"{student['first_name']} {student['last_name']}",
            "enrolled_at": now,
            "status": "active",
        })
    for e in enrollments:
        _enrollments_db[e["id"]] = e
    print(f"[seed] {len(enrollments)} enrollments created.")


def seed_grades(r: random.Random) -> None:
    """Seed grade entries for students."""
    student_ids = list(_students_db.keys())
    subjects_pool = ["Mathematics", "Science", "English", "AP", "MAPEH"]
    now = str(datetime.utcnow())
    grades = []
    for sid in student_ids:
        subject = r.choice(subjects_pool)
        score = round(r.uniform(60, 100), 1)
        grades.append({
            "id": str(uuid4()),
            "student_id": sid,
            "subject": subject,
            "quarter": 1,
            "score": score,
            "max_score": 100,
            "weight": None,
            "remarks": "Passed" if score >= 75 else "Failed",
            "graded_by": "u-teacher-001",
            "school_year": "2026-2027",
        })
    for g in grades:
        _grades_db[g["id"]] = g
    print(f"[seed] {len(grades)} grade entries created.")


def seed_attendance(r: random.Random) -> None:
    """Seed attendance records."""
    student_ids = list(_students_db.keys())
    now = str(datetime.utcnow())
    statuses = ["present", "absent", "late", "excused"]
    records = []
    for sid in student_ids:
        for day in range(1, 21):
            records.append({
                "id": str(uuid4()),
                "student_id": sid,
                "date": (datetime.utcnow() - timedelta(days=30 - day)).strftime("%Y-%m-%d"),
                "status": r.choices(statuses, weights=[80, 8, 7, 5], k=1)[0],
                "remarks": None if r.random() > 0.1 else "No remarks",
                "recorded_by": "u-teacher-001",
                "created_at": now,
            })
    for rec in records:
        _attendance_db[rec["id"]] = rec
    print(f"[seed] {len(records)} attendance records created.")


def seed_reports(r: random.Random) -> None:
    """Seed report templates."""
    now = str(datetime.utcnow())
    reports = [
        {
            "id": "r-rpms-001",
            "title": "RPMS Sy 2026-2027",
            "report_type": "rpms",
            "school_year": "2026-2027",
            "quarter": 1,
            "status": "draft",
            "created_by": "u-teacher-001",
            "data": {},
            "remarks": None,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "r-monthly-001",
            "title": "Monthly Accomplishment — September",
            "report_type": "sf2",
            "school_year": "2026-2027",
            "quarter": 1,
            "status": "draft",
            "created_by": "u-teacher-001",
            "data": {},
            "remarks": None,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "r-narrative-001",
            "title": "Narrative Report — Science Fair",
            "report_type": "custom",
            "school_year": "2026-2027",
            "quarter": 1,
            "status": "submitted",
            "created_by": "u-teacher-001",
            "data": {},
            "remarks": None,
            "created_at": now,
            "updated_at": now,
        },
        {
            "id": "r-narrative-002",
            "title": "Quarterly Assessment Analysis",
            "report_type": "sf5",
            "school_year": "2026-2027",
            "quarter": 1,
            "status": "draft",
            "created_by": "u-teacher-001",
            "data": {},
            "remarks": None,
            "created_at": now,
            "updated_at": now,
        },
    ]
    for rep in reports:
        _reports_db[rep["id"]] = rep
    print(f"[seed] {len(reports)} reports created.")


def seed_forms(r: random.Random) -> None:
    """Seed school form templates."""
    now = str(datetime.utcnow())
    forms = [
        {
            "id": "f-sf1-001",
            "name": "School Register (SF1)",
            "form_type": "sf1",
            "version": "1.0",
            "description": "Official school register form for Grade 6 - Sampaguita",
            "fields": [],
            "is_active": True,
        },
        {
            "id": "f-sf2-001",
            "name": "Daily Attendance Report (SF2)",
            "form_type": "sf2",
            "version": "1.0",
            "description": "Daily attendance report for Grade 6 - Sampaguita",
            "fields": [],
            "is_active": True,
        },
        {
            "id": "f-sf5-001",
            "name": "Promotion Report (SF5)",
            "form_type": "sf5",
            "version": "1.0",
            "description": "Promotion and graduation report",
            "fields": [],
            "is_active": True,
        },
        {
            "id": "f-sf9-001",
            "name": "Learner Progress Report (SF9)",
            "form_type": "sf9",
            "version": "1.0",
            "description": "Quarterly learner progress report card",
            "fields": [],
            "is_active": True,
        },
        {
            "id": "f-sf10-001",
            "name": "Learner Permanent Record (SF10)",
            "form_type": "sf10",
            "version": "1.0",
            "description": "Learner's permanent academic record",
            "fields": [],
            "is_active": True,
        },
    ]
    for f in forms:
        _forms_db[f["id"]] = f
    print(f"[seed] {len(forms)} form templates created.")