from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, time
from uuid import UUID

from sqlmodel import Session, select

SCRIPT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "src"))
sys.path.append(SRC_DIR)
BASE_DATA_DIR = os.path.join(SCRIPT_DIR, "data")

from db import engine  # noqa: E402
from models.academic_class import AcademicClass  # noqa: E402
from models.academic_class_subject import AcademicClassSubject  # noqa: E402
from models.academic_session import AcademicSession  # noqa: E402
from models.academic_term import AcademicTerm, AcademicTermType  # noqa: E402
from models.date_sheet import DateSheet  # noqa: E402
from models.date_sheet_subject import DateSheetSubject  # noqa: E402
from models.enrollment import Enrollment  # noqa: E402
from models.report_card import (  # noqa: E402
    ReportCard,
    ReportCardGrade,
    ReportCardResult,
)
from models.report_card_subject import ReportCardSubject  # noqa: E402
from models.student import Student  # noqa: E402
from models.subject import Subject  # noqa: E402
from models.user import User, UserRole  # noqa: E402


def load_json(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_created_at(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def parse_optional_time(value: str | None) -> time | None:
    if not value:
        return None
    return time.fromisoformat(value)


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
    work_education_grade: ReportCardGrade | None,
    art_education_grade: ReportCardGrade | None,
    physical_education_grade: ReportCardGrade | None,
    behaviour_grade: ReportCardGrade | None,
    attendance_present: int | None,
    result: ReportCardResult | None,
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
        work_education_grade=work_education_grade,
        art_education_grade=art_education_grade,
        physical_education_grade=physical_education_grade,
        behaviour_grade=behaviour_grade,
        attendance_present=attendance_present,
        result=result,
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


def get_or_create_date_sheet(
    session: Session,
    date_sheet_id: UUID,
    academic_class_id: UUID,
    academic_term_id: UUID,
    created_at: datetime,
) -> tuple[DateSheet, bool]:
    existing = session.get(DateSheet, date_sheet_id)
    if existing:
        return existing, False

    statement = select(DateSheet).where(
        DateSheet.academic_class_id == academic_class_id,
        DateSheet.academic_term_id == academic_term_id,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    date_sheet = DateSheet(
        id=date_sheet_id,
        academic_class_id=academic_class_id,
        academic_term_id=academic_term_id,
        created_at=created_at,
    )
    session.add(date_sheet)
    session.commit()
    session.refresh(date_sheet)
    return date_sheet, True


def get_or_create_date_sheet_subject(
    session: Session,
    date_sheet_subject_id: UUID,
    date_sheet_id: UUID,
    academic_class_subject_id: UUID,
    paper_code: str | None,
    exam_date: date | None,
    start_time: time | None,
    end_time: time | None,
    created_at: datetime,
) -> tuple[DateSheetSubject, bool]:
    existing = session.get(DateSheetSubject, date_sheet_subject_id)
    if existing:
        return existing, False

    statement = select(DateSheetSubject).where(
        DateSheetSubject.date_sheet_id == date_sheet_id,
        DateSheetSubject.academic_class_subject_id
        == academic_class_subject_id,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    date_sheet_subject = DateSheetSubject(
        id=date_sheet_subject_id,
        date_sheet_id=date_sheet_id,
        academic_class_subject_id=academic_class_subject_id,
        paper_code=paper_code,
        exam_date=exam_date,
        start_time=start_time,
        end_time=end_time,
        created_at=created_at,
    )
    session.add(date_sheet_subject)
    session.commit()
    session.refresh(date_sheet_subject)
    return date_sheet_subject, True


def get_or_create_user(
    session: Session,
    user_id: UUID,
    email: str,
    role: UserRole,
    default_academic_session_id: UUID | None,
    default_academic_term_id: UUID | None,
    default_academic_class_id: UUID | None,
    created_at: datetime,
) -> tuple[User, bool]:
    existing = session.get(User, user_id)
    if existing:
        return existing, False

    statement = select(User).where(User.email == email)
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    user = User(
        id=user_id,
        email=email,
        role=role,
        default_academic_session_id=default_academic_session_id,
        default_academic_term_id=default_academic_term_id,
        default_academic_class_id=default_academic_class_id,
        created_at=created_at,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user, True


def seed_students(
    session: Session,
    data_dir: str,
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
    date_sheet_inserted = 0
    date_sheet_skipped = 0
    date_sheet_subject_inserted = 0
    date_sheet_subject_skipped = 0
    user_inserted = 0
    user_skipped = 0

    academic_sessions = load_json(
        os.path.join(data_dir, "academic_sessions.json")
    )
    academic_terms = load_json(
        os.path.join(data_dir, "academic_terms.json")
    )
    academic_classes = load_json(
        os.path.join(data_dir, "academic_classes.json")
    )
    students = load_json(os.path.join(data_dir, "students.json"))
    enrollments = load_json(
        os.path.join(data_dir, "enrollments.json")
    )
    subjects = load_json(os.path.join(data_dir, "subjects.json"))
    academic_class_subjects = load_json(
        os.path.join(data_dir, "academic_class_subjects.json")
    )
    report_cards = load_json(os.path.join(data_dir, "report_cards.json"))
    report_card_subjects = load_json(
        os.path.join(data_dir, "report_card_subjects.json")
    )
    date_sheets = load_json(os.path.join(data_dir, "date_sheets.json"))
    date_sheet_subjects = load_json(
        os.path.join(data_dir, "date_sheet_subjects.json")
    )
    users = load_json(os.path.join(data_dir, "users.json"))

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
            position=raw["position"],
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
            work_education_grade=ReportCardGrade(raw["work_education_grade"])
            if raw.get("work_education_grade")
            else None,
            art_education_grade=ReportCardGrade(raw["art_education_grade"])
            if raw.get("art_education_grade")
            else None,
            physical_education_grade=ReportCardGrade(
                raw["physical_education_grade"]
            )
            if raw.get("physical_education_grade")
            else None,
            behaviour_grade=ReportCardGrade(raw["behaviour_grade"])
            if raw.get("behaviour_grade")
            else None,
            attendance_present=raw.get("attendance_present"),
            result=ReportCardResult(raw["result"])
            if raw.get("result")
            else None,
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

    for raw in date_sheets:
        date_sheet_id = UUID(raw["id"])
        _, created = get_or_create_date_sheet(
            session=session,
            date_sheet_id=date_sheet_id,
            academic_class_id=UUID(raw["academic_class_id"]),
            academic_term_id=UUID(raw["academic_term_id"]),
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            date_sheet_inserted += 1
        else:
            date_sheet_skipped += 1

    for raw in date_sheet_subjects:
        date_sheet_subject_id = UUID(raw["id"])
        _, created = get_or_create_date_sheet_subject(
            session=session,
            date_sheet_subject_id=date_sheet_subject_id,
            date_sheet_id=UUID(raw["date_sheet_id"]),
            academic_class_subject_id=UUID(
                raw["academic_class_subject_id"]
            ),
            paper_code=raw.get("paper_code"),
            exam_date=parse_optional_date(raw.get("exam_date")),
            start_time=parse_optional_time(raw.get("start_time")),
            end_time=parse_optional_time(raw.get("end_time")),
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            date_sheet_subject_inserted += 1
        else:
            date_sheet_subject_skipped += 1

    for raw in users:
        user_id = UUID(raw["id"])
        _, created = get_or_create_user(
            session=session,
            user_id=user_id,
            email=raw["email"],
            role=UserRole(raw["role"]),
            default_academic_session_id=UUID(
                raw["default_academic_session_id"])
            if raw.get("default_academic_session_id")
            else None,
            default_academic_term_id=UUID(raw["default_academic_term_id"])
            if raw.get("default_academic_term_id")
            else None,
            default_academic_class_id=UUID(raw["default_academic_class_id"])
            if raw.get("default_academic_class_id")
            else None,
            created_at=parse_created_at(raw["created_at"]),
        )
        if created:
            user_inserted += 1
        else:
            user_skipped += 1

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
        (date_sheet_inserted, date_sheet_skipped),
        (date_sheet_subject_inserted, date_sheet_subject_skipped),
        (user_inserted, user_skipped),
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed database using JSON files."
    )
    parser.add_argument(
        "--data-name",
        required=True,
        help="Seed data folder name under seeders/data",
    )
    args = parser.parse_args()

    data_dir = os.path.join(BASE_DATA_DIR, args.data_name)

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
            (date_sheet_inserted, date_sheet_skipped),
            (date_sheet_subject_inserted, date_sheet_subject_skipped),
            (user_inserted, user_skipped),
        ) = seed_students(session, data_dir)

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
    print(
        "Seeded date sheets.",
        f"Inserted: {date_sheet_inserted}.",
        f"Skipped (already existed): {date_sheet_skipped}.",
    )
    print(
        "Seeded date sheet subjects.",
        f"Inserted: {date_sheet_subject_inserted}.",
        f"Skipped (already existed): {date_sheet_subject_skipped}.",
    )
    print(
        "Seeded users.",
        f"Inserted: {user_inserted}.",
        f"Skipped (already existed): {user_skipped}.",
    )
