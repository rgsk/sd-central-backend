from __future__ import annotations

import json
import os
import sys
from datetime import date
from uuid import UUID

from sqlmodel import Session, select

SCRIPT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "src"))
sys.path.append(SRC_DIR)
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

from db import engine  # noqa: E402
from models.academic_class import AcademicClass  # noqa: E402
from models.student import Student  # noqa: E402


def load_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_or_create_academic_class(
    session: Session,
    academic_session: str,
    class_id: UUID,
    grade: str,
    section: str,
) -> tuple[AcademicClass, bool]:
    existing = session.get(AcademicClass, class_id)
    if existing:
        return existing, False

    statement = select(AcademicClass).where(
        AcademicClass.session == academic_session,
        AcademicClass.grade == grade,
        AcademicClass.section == section,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    academic_class = AcademicClass(
        id=class_id,
        session=academic_session,
        grade=grade,
        section=section,
    )
    session.add(academic_class)
    session.commit()
    session.refresh(academic_class)
    return academic_class, True


def seed_students(
    session: Session,
) -> tuple[tuple[int, int], tuple[int, int]]:
    class_inserted = 0
    class_skipped = 0
    student_inserted = 0
    student_skipped = 0
    class_map: dict[UUID, AcademicClass] = {}

    academic_classes = load_json(
        os.path.join(DATA_DIR, "academic_classes.json"))
    students = load_json(os.path.join(DATA_DIR, "students.json"))

    for raw in academic_classes:
        class_id = UUID(raw["id"])
        academic_class, created = get_or_create_academic_class(
            session,
            raw["session"],
            class_id,
            raw["grade"],
            raw["section"],
        )
        if created:
            class_inserted += 1
        else:
            class_skipped += 1
        class_map[class_id] = academic_class

    for raw in students:
        class_id = UUID(raw["academic_class_id"])
        academic_class = class_map[class_id]

        student_id = UUID(raw["id"])
        existing = session.get(Student, student_id)
        if existing:
            student_skipped += 1
            continue

        student = Student(
            id=student_id,
            registration_no=raw["registration_no"],
            name=raw["name"],
            academic_class_id=academic_class.id,
            dob=date.fromisoformat(raw['dob']),
            father_name=raw["father_name"],
            mother_name=raw["mother_name"],
            image=raw.get("image"),
        )
        session.add(student)
        student_inserted += 1

    session.commit()
    return (class_inserted, class_skipped), (student_inserted, student_skipped)


if __name__ == "__main__":

    with Session(engine) as session:
        (class_inserted, class_skipped), (student_inserted, student_skipped) = (
            seed_students(
                session,
            )
        )

    print(
        "Seeded academic classes.",
        f"Inserted: {class_inserted}.",
        f"Skipped (already existed): {class_skipped}.",
    )
    print(
        "Seeded students.",
        f"Inserted: {student_inserted}.",
        f"Skipped (already existed): {student_skipped}.",
    )
