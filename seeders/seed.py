from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime
from uuid import UUID

from sqlmodel import Session, select

SCRIPT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "src"))
sys.path.append(SRC_DIR)
DATA_DIR = os.path.join(SCRIPT_DIR, "data")

from db import engine  # noqa: E402
from models.academic_class import AcademicClass  # noqa: E402
from models.academic_class_subject import AcademicClassSubject  # noqa: E402
from models.academic_session import AcademicSession  # noqa: E402
from models.academic_term import AcademicTerm, AcademicTermType  # noqa: E402
from models.enrollment import Enrollment  # noqa: E402
from models.report_card import ReportCard  # noqa: E402
from models.report_card_subject import ReportCardSubject  # noqa: E402
from models.student import Student  # noqa: E402
from models.subject import Subject  # noqa: E402


def load_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_created_at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def get_or_create_academic_class(
    session: Session,
    academic_session_id: UUID,
    academic_class_id: UUID,
    grade: str,
    section: str,
    created_at: datetime,
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
        created_at=created_at,
    )
    session.add(academic_class)
    session.commit()
    session.refresh(academic_class)
    return academic_class, True


def get_or_create_academic_session(
    session: Session,
    year: str,
    academic_session_id: UUID,
    created_at: datetime,
) -> tuple[AcademicSession, bool]:
    existing = session.get(AcademicSession, academic_session_id)
    if existing:
        return existing, False

    statement = select(AcademicSession).where(AcademicSession.year == year)
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    academic_session = AcademicSession(
        id=academic_session_id,
        year=year,
        created_at=created_at,
    )
    session.add(academic_session)
    session.commit()
    session.refresh(academic_session)
    return academic_session, True


def get_or_create_student(
    session: Session,
    student_id: UUID,
    registration_no: str,
    name: str,
    dob: date,
    father_name: str,
    mother_name: str,
    created_at: datetime,
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
        dob=dob,
        father_name=father_name,
        mother_name=mother_name,
        created_at=created_at,
    )
    session.add(student)
    return student, True


def get_or_create_enrollment(
    session: Session,
    enrollment_id: UUID,
    student_id: UUID,
    academic_session_id: UUID,
    academic_class_id: UUID,
    image: str | None,
    created_at: datetime,
) -> tuple[Enrollment, bool]:
    existing = session.get(Enrollment, enrollment_id)
    if existing:
        return existing, False

    statement = select(Enrollment).where(
        Enrollment.student_id == student_id,
        Enrollment.academic_class_id == academic_class_id,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    enrollment = Enrollment(
        id=enrollment_id,
        student_id=student_id,
        academic_session_id=academic_session_id,
        academic_class_id=academic_class_id,
        image=image,
        created_at=created_at,
    )
    session.add(enrollment)
    session.commit()
    session.refresh(enrollment)
    return enrollment, True


def get_or_create_academic_term(
    session: Session,
    academic_term_id: UUID,
    academic_session_id: UUID,
    term_type: AcademicTermType,
    working_days: int | None,
    exam_result_date: date | None,
    created_at: datetime,
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
        working_days=working_days,
        exam_result_date=exam_result_date,
        created_at=created_at,
    )
    session.add(academic_term)
    session.commit()
    session.refresh(academic_term)
    return academic_term, True


def get_or_create_subject(
    session: Session,
    subject_id: UUID,
    name: str,
    created_at: datetime,
) -> tuple[Subject, bool]:
    existing = session.get(Subject, subject_id)
    if existing:
        return existing, False

    statement = select(Subject).where(Subject.name == name)
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    subject = Subject(id=subject_id, name=name, created_at=created_at)
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject, True


def get_or_create_academic_class_subject(
    session: Session,
    academic_class_subject_id: UUID,
    academic_class_id: UUID,
    subject_id: UUID,
    academic_term_id: UUID,
    highest_marks: int | None,
    average_marks: int | None,
    is_additional: bool,
    position: int,
    created_at: datetime,
) -> tuple[AcademicClassSubject, bool]:
    existing = session.get(AcademicClassSubject, academic_class_subject_id)
    if existing:
        return existing, False

    statement = select(AcademicClassSubject).where(
        AcademicClassSubject.academic_class_id == academic_class_id,
        AcademicClassSubject.subject_id == subject_id,
        AcademicClassSubject.academic_term_id == academic_term_id,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    class_subject = AcademicClassSubject(
        id=academic_class_subject_id,
        academic_class_id=academic_class_id,
        subject_id=subject_id,
        academic_term_id=academic_term_id,
        highest_marks=highest_marks,
        average_marks=average_marks,
        is_additional=is_additional,
        position=position,
        created_at=created_at,
    )
    session.add(class_subject)
    session.commit()
    session.refresh(class_subject)
    return class_subject, True


def get_or_create_report_card(
    session: Session,
    report_card_id: UUID,
    enrollment_id: UUID,
    academic_term_id: UUID,
    created_at: datetime,
) -> tuple[ReportCard, bool]:
    existing = session.get(ReportCard, report_card_id)
    if existing:
        return existing, False

    statement = select(ReportCard).where(
        ReportCard.enrollment_id == enrollment_id,
        ReportCard.academic_term_id == academic_term_id,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    report_card = ReportCard(
        id=report_card_id,
        enrollment_id=enrollment_id,
        academic_term_id=academic_term_id,
        created_at=created_at,
    )
    session.add(report_card)
    session.commit()
    session.refresh(report_card)
    return report_card, True


def get_or_create_report_card_subject(
    session: Session,
    report_card_subject_id: UUID,
    report_card_id: UUID,
    academic_class_subject_id: UUID,
    mid_term: int | None,
    notebook: int | None,
    assignment: int | None,
    class_test: int | None,
    final_term: int | None,
    final_marks: int | None,
    created_at: datetime,
) -> tuple[ReportCardSubject, bool]:
    existing = session.get(ReportCardSubject, report_card_subject_id)
    if existing:
        return existing, False

    statement = select(ReportCardSubject).where(
        ReportCardSubject.report_card_id == report_card_id,
        ReportCardSubject.academic_class_subject_id
        == academic_class_subject_id,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    report_card_subject = ReportCardSubject(
        id=report_card_subject_id,
        report_card_id=report_card_id,
        academic_class_subject_id=academic_class_subject_id,
        mid_term=mid_term,
        notebook=notebook,
        assignment=assignment,
        class_test=class_test,
        final_term=final_term,
        final_marks=final_marks,
        created_at=created_at,
    )
    session.add(report_card_subject)
    session.commit()
    session.refresh(report_card_subject)
    return report_card_subject, True


def seed_students(
    session: Session,
) -> tuple[
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
    tuple[int, int],
]:
    class_inserted = 0
    class_skipped = 0
    session_inserted = 0
    session_skipped = 0
    term_inserted = 0
    term_skipped = 0
    student_inserted = 0
    student_skipped = 0
    enrollment_inserted = 0
    enrollment_skipped = 0
    subject_inserted = 0
    subject_skipped = 0
    class_subject_inserted = 0
    class_subject_skipped = 0
    report_card_inserted = 0
    report_card_skipped = 0
    report_card_subject_inserted = 0
    report_card_subject_skipped = 0

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
    enrollments = load_json(
        os.path.join(DATA_DIR, "enrollments.json")
    )
    subjects = load_json(os.path.join(DATA_DIR, "subjects.json"))
    academic_class_subjects = load_json(
        os.path.join(DATA_DIR, "academic_class_subjects.json")
    )
    report_cards = load_json(os.path.join(DATA_DIR, "report_cards.json"))
    report_card_subjects = load_json(
        os.path.join(DATA_DIR, "report_card_subjects.json")
    )

    session_map: dict[UUID, AcademicSession] = {}
    for raw in academic_sessions:
        academic_session_id = UUID(raw["id"])
        academic_session, created = get_or_create_academic_session(
            session=session,
            year=raw["year"],
            academic_session_id=academic_session_id,
            created_at=parse_created_at(raw["created_at"]),
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
            working_days=raw.get("working_days"),
            exam_result_date=parse_optional_date(
                raw.get("exam_result_date")
            ),
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            term_inserted += 1
        else:
            term_skipped += 1

    for raw in academic_classes:
        academic_session_id = UUID(raw["academic_session_id"])
        academic_class_id = UUID(raw["id"])
        academic_class, created = get_or_create_academic_class(
            session=session,
            academic_session_id=academic_session_id,
            academic_class_id=academic_class_id,
            grade=raw["grade"],
            section=raw["section"],
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            class_inserted += 1
        else:
            class_skipped += 1

    for raw in subjects:
        subject_id = UUID(raw["id"])
        _, created = get_or_create_subject(
            session=session,
            subject_id=subject_id,
            name=raw["name"],
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            subject_inserted += 1
        else:
            subject_skipped += 1

    for raw in academic_class_subjects:
        academic_class_subject_id = UUID(raw["id"])
        _, created = get_or_create_academic_class_subject(
            session=session,
            academic_class_subject_id=academic_class_subject_id,
            academic_class_id=UUID(raw["academic_class_id"]),
            subject_id=UUID(raw["subject_id"]),
            academic_term_id=UUID(raw["academic_term_id"]),
            highest_marks=raw.get("highest_marks"),
            average_marks=raw.get("average_marks"),
            is_additional=raw.get("is_additional", False),
            position=raw.get("position", 1),
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            class_subject_inserted += 1
        else:
            class_subject_skipped += 1

    for raw in students:
        student_id = UUID(raw["id"])
        student, created = get_or_create_student(
            session=session,
            student_id=student_id,
            registration_no=raw["registration_no"],
            name=raw["name"],
            dob=date.fromisoformat(raw["dob"]),
            father_name=raw["father_name"],
            mother_name=raw["mother_name"],
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            student_inserted += 1
        else:
            student_skipped += 1

    for raw in enrollments:
        enrollment_id = UUID(raw["id"])
        enrollment, created = get_or_create_enrollment(
            session=session,
            enrollment_id=enrollment_id,
            student_id=UUID(raw["student_id"]),
            academic_session_id=UUID(raw["academic_session_id"]),
            academic_class_id=UUID(raw["academic_class_id"]),
            image=raw.get("image"),
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            enrollment_inserted += 1
        else:
            enrollment_skipped += 1

    for raw in report_cards:
        report_card_id = UUID(raw["id"])
        _, created = get_or_create_report_card(
            session=session,
            report_card_id=report_card_id,
            enrollment_id=UUID(raw["enrollment_id"]),
            academic_term_id=UUID(raw["academic_term_id"]),
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            report_card_inserted += 1
        else:
            report_card_skipped += 1

    for raw in report_card_subjects:
        report_card_subject_id = UUID(raw["id"])
        _, created = get_or_create_report_card_subject(
            session=session,
            report_card_subject_id=report_card_subject_id,
            report_card_id=UUID(raw["report_card_id"]),
            academic_class_subject_id=UUID(
                raw["academic_class_subject_id"]
            ),
            mid_term=raw.get("mid_term"),
            notebook=raw.get("notebook"),
            assignment=raw.get("assignment"),
            class_test=raw.get("class_test"),
            final_term=raw.get("final_term"),
            final_marks=raw.get("final_marks"),
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            report_card_subject_inserted += 1
        else:
            report_card_subject_skipped += 1

    session.commit()
    return (
        (session_inserted, session_skipped),
        (term_inserted, term_skipped),
        (class_inserted, class_skipped),
        (student_inserted, student_skipped),
        (enrollment_inserted, enrollment_skipped),
        (subject_inserted, subject_skipped),
        (class_subject_inserted, class_subject_skipped),
        (report_card_inserted, report_card_skipped),
        (report_card_subject_inserted, report_card_subject_skipped),
    )


if __name__ == "__main__":

    with Session(engine) as session:
        (
            (session_inserted, session_skipped),
            (term_inserted, term_skipped),
            (class_inserted, class_skipped),
            (student_inserted, student_skipped),
            (enrollment_inserted, enrollment_skipped),
            (subject_inserted, subject_skipped),
            (class_subject_inserted, class_subject_skipped),
            (report_card_inserted, report_card_skipped),
            (report_card_subject_inserted, report_card_subject_skipped),
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
    print(
        "Seeded enrollments.",
        f"Inserted: {enrollment_inserted}.",
        f"Skipped (already existed): {enrollment_skipped}.",
    )
    print(
        "Seeded subjects.",
        f"Inserted: {subject_inserted}.",
        f"Skipped (already existed): {subject_skipped}.",
    )
    print(
        "Seeded academic class subjects.",
        f"Inserted: {class_subject_inserted}.",
        f"Skipped (already existed): {class_subject_skipped}.",
    )
    print(
        "Seeded report cards.",
        f"Inserted: {report_card_inserted}.",
        f"Skipped (already existed): {report_card_skipped}.",
    )
    print(
        "Seeded report card subjects.",
        f"Inserted: {report_card_subject_inserted}.",
        f"Skipped (already existed): {report_card_subject_skipped}.",
    )
