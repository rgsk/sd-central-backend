from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from uuid import UUID

from seed_data import STUDENTS
from sqlmodel import Session, select

SCRIPT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "src"))
sys.path.append(SRC_DIR)

from db import engine  # noqa: E402
from models.academic_class import AcademicClass  # noqa: E402
from models.student import Student  # noqa: E402

DEFAULT_DOB = date(2019, 1, 1)
DEFAULT_SESSION = "2024-2025"
DEFAULT_MOTHER_NAME = "UNKNOWN"


def get_or_create_academic_class(
    session: Session,
    academic_session: str,
    class_value: str,
    section: str,
) -> AcademicClass:
    statement = select(AcademicClass).where(
        AcademicClass.session == academic_session,
        AcademicClass.class_value == class_value,
        AcademicClass.section == section,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing

    academic_class = AcademicClass(
        session=academic_session,
        class_value=class_value,
        section=section,
    )
    session.add(academic_class)
    session.commit()
    session.refresh(academic_class)
    return academic_class


def parse_dob(raw_value: str | None, default_dob: date) -> date:
    if not raw_value:
        return default_dob
    return date.fromisoformat(raw_value)


def seed_students(
    session: Session,
    academic_session: str,
    default_dob: date,
) -> tuple[int, int]:
    inserted = 0
    skipped = 0

    for raw in STUDENTS:
        academic_class = get_or_create_academic_class(
            session,
            academic_session,
            raw["Class"].strip(),
            raw["Section"].strip(),
        )

        student_id = UUID(raw["id"])
        existing = session.get(Student, student_id)
        if existing:
            skipped += 1
            continue

        student = Student(
            id=student_id,
            registration_no=raw["Regn. No."].strip(),
            name=raw["Student Name"].strip(),
            academic_class_id=academic_class.id,
            dob=parse_dob(raw.get("Date of Birth"), default_dob),
            father_name=raw.get("Father's Name", "").strip(),
            mother_name=raw.get("Mother's Name", DEFAULT_MOTHER_NAME).strip()
            or DEFAULT_MOTHER_NAME,
            image=raw.get("studentImage"),
        )
        session.add(student)
        inserted += 1

    session.commit()
    return inserted, skipped


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed academic classes and students."
    )
    parser.add_argument(
        "--session",
        default=DEFAULT_SESSION,
        help="Academic session value (default: 2024-2025)",
    )
    parser.add_argument(
        "--default-dob",
        default=str(DEFAULT_DOB),
        help="Default DOB for records without one (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    with Session(engine) as session:
        inserted, skipped = seed_students(
            session,
            args.session,
            date.fromisoformat(args.default_dob),
        )

    print(
        "Seeded students.",
        f"Inserted: {inserted}.",
        f"Skipped (already existed): {skipped}.",
    )
