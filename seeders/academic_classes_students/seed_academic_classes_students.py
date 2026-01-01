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
from models.academic_session import AcademicSession  # noqa: E402
from models.academic_term import AcademicTerm, AcademicTermType  # noqa: E402
from models.student import Student  # noqa: E402


def load_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def get_or_create_academic_class(
    session: Session,
    academic_session_id: UUID,
    academic_class_id: UUID,
    grade: str,
    section: str,
) -> tuple[AcademicClass, bool]:
    existing = session.get(AcademicClass, academic_class_id)
    if existing:
        return existing, False

    statement = select(AcademicClass).where(
        AcademicClass.academic_session_id == academic_session_id,
        AcademicClass.grade == grade,
        AcademicClass.section == section,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    academic_class = AcademicClass(
        id=academic_class_id,
        academic_session_id=academic_session_id,
        grade=grade,
        section=section,
    )
    session.add(academic_class)
    session.commit()
    session.refresh(academic_class)
    return academic_class, True


def get_or_create_academic_session(
    session: Session,
    year: str,
    academic_session_id: UUID,
) -> tuple[AcademicSession, bool]:
    existing = session.get(AcademicSession, academic_session_id)
    if existing:
        return existing, False

    statement = select(AcademicSession).where(AcademicSession.year == year)
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    academic_session = AcademicSession(id=academic_session_id, year=year)
    session.add(academic_session)
    session.commit()
    session.refresh(academic_session)
    return academic_session, True


def get_or_create_student(
    session: Session,
    student_id: UUID,
    registration_no: str,
    name: str,
    academic_class_id: UUID,
    dob: date,
    father_name: str,
    mother_name: str,
    image: str | None,
) -> tuple[Student, bool]:
    existing = session.get(Student, student_id)
    if existing:
        return existing, False

    statement = select(Student).where(
        Student.registration_no == registration_no)
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    student = Student(
        id=student_id,
        registration_no=registration_no,
        name=name,
        academic_class_id=academic_class_id,
        dob=dob,
        father_name=father_name,
        mother_name=mother_name,
        image=image,
    )
    session.add(student)
    return student, True


def get_or_create_academic_term(
    session: Session,
    academic_term_id: UUID,
    academic_session_id: UUID,
    term_type: AcademicTermType,
) -> tuple[AcademicTerm, bool]:
    existing = session.get(AcademicTerm, academic_term_id)
    if existing:
        return existing, False

    statement = select(AcademicTerm).where(
        AcademicTerm.academic_session_id == academic_session_id,
        AcademicTerm.term_type == term_type,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    academic_term = AcademicTerm(
        id=academic_term_id,
        academic_session_id=academic_session_id,
        term_type=term_type,
    )
    session.add(academic_term)
    session.commit()
    session.refresh(academic_term)
    return academic_term, True


def seed_students(
    session: Session,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
    class_inserted = 0
    class_skipped = 0
    session_inserted = 0
    session_skipped = 0
    term_inserted = 0
    term_skipped = 0
    student_inserted = 0
    student_skipped = 0
    class_map: dict[UUID, AcademicClass] = {}

    academic_sessions = load_json(
        os.path.join(DATA_DIR, "academic_sessions.json")
    )
    academic_terms = load_json(
        os.path.join(DATA_DIR, "academic_terms.json")
    )
    academic_classes = load_json(
        os.path.join(DATA_DIR, "academic_classes.json")
    )
    students = load_json(os.path.join(DATA_DIR, "students.json"))

    session_map: dict[UUID, AcademicSession] = {}
    for raw in academic_sessions:
        academic_session_id = UUID(raw["id"])
        academic_session, created = get_or_create_academic_session(
            session=session,
            year=raw["year"],
            academic_session_id=academic_session_id,
        )
        if created:
            session_inserted += 1
        else:
            session_skipped += 1
        session_map[academic_session_id] = academic_session

    for raw in academic_terms:
        academic_term_id = UUID(raw["id"])
        academic_term, created = get_or_create_academic_term(
            session=session,
            academic_term_id=academic_term_id,
            academic_session_id=UUID(raw["academic_session_id"]),
            term_type=AcademicTermType(raw["term_type"]),
        )
        if created:
            term_inserted += 1
        else:
            term_skipped += 1

    for raw in academic_classes:
        academic_session_id = UUID(raw["academic_session_id"])
        academic_session = session_map[academic_session_id]
        academic_class_id = UUID(raw["id"])
        academic_class, created = get_or_create_academic_class(
            session=session,
            academic_session_id=academic_session_id,
            academic_class_id=academic_class_id,
            grade=raw["grade"],
            section=raw["section"],
        )
        if created:
            class_inserted += 1
        else:
            class_skipped += 1
        class_map[academic_class_id] = academic_class

    for raw in students:
        academic_class_id = UUID(raw["academic_class_id"])
        academic_class = class_map[academic_class_id]

        student_id = UUID(raw["id"])
        student, created = get_or_create_student(
            session=session,
            student_id=student_id,
            registration_no=raw["registration_no"],
            name=raw["name"],
            academic_class_id=academic_class_id,
            dob=date.fromisoformat(raw["dob"]),
            father_name=raw["father_name"],
            mother_name=raw["mother_name"],
            image=raw.get("image"),
        )
        if created:
            student_inserted += 1
        else:
            student_skipped += 1

    session.commit()
    return (
        (session_inserted, session_skipped),
        (term_inserted, term_skipped),
        (class_inserted, class_skipped),
        (student_inserted, student_skipped),
    )


if __name__ == "__main__":

    with Session(engine) as session:
        (
            (session_inserted, session_skipped),
            (term_inserted, term_skipped),
            (class_inserted, class_skipped),
            (student_inserted, student_skipped),
        ) = seed_students(session)

    print(
        "Seeded academic sessions.",
        f"Inserted: {session_inserted}.",
        f"Skipped (already existed): {session_skipped}.",
    )
    print(
        "Seeded academic terms.",
        f"Inserted: {term_inserted}.",
        f"Skipped (already existed): {term_skipped}.",
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
