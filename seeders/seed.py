from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime, time
from time import perf_counter
from uuid import UUID

from sqlalchemy import exists, insert, or_
from sqlmodel import Session, select

SCRIPT_DIR = os.path.dirname(__file__)
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "src"))
sys.path.append(SRC_DIR)
BASE_DATA_DIR = os.path.join(SCRIPT_DIR, "data")

from db import engine, normalize_db_namespace  # noqa: E402
from models.academic_class import AcademicClass  # noqa: E402
from models.academic_class_subject import AcademicClassSubject  # noqa: E402
from models.academic_class_subject_term import \
    AcademicClassSubjectTerm  # noqa: E402
from models.academic_session import AcademicSession  # noqa: E402
from models.academic_term import AcademicTerm, AcademicTermType  # noqa: E402
from models.date_sheet import DateSheet  # noqa: E402
from models.date_sheet_subject import DateSheetSubject  # noqa: E402
from models.enrollment import Enrollment  # noqa: E402
from models.report_card import (ReportCard, ReportCardGrade,  # noqa: E402
                                ReportCardResult)
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


def seed_students(
    session: Session,
    data_dir: str,
) -> None:
    start_time = perf_counter()

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
    academic_class_subject_terms = load_json(
        os.path.join(data_dir, "academic_class_subject_terms.json")
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

    def assert_db_is_empty() -> None:
        tables = [
            AcademicSession,
            AcademicTerm,
            AcademicClass,
            Subject,
            AcademicClassSubject,
            AcademicClassSubjectTerm,
            Student,
            Enrollment,
            ReportCard,
            ReportCardSubject,
            DateSheet,
            DateSheetSubject,
            User,
        ]
        any_rows = session.exec(
            select(or_(*[exists().select_from(model) for model in tables]))
        ).one()
        if any_rows:
            raise RuntimeError("Seed expects an empty database.")

    def insert_rows(model: type, rows: list[dict]) -> int:
        if not rows:
            return 0
        session.execute(insert(model), rows)
        return len(rows)

    assert_db_is_empty()

    section_start = perf_counter()
    session_rows = [
        {
            "id": UUID(raw["id"]),
            "year": raw["year"],
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in academic_sessions
    ]
    session_inserted = insert_rows(AcademicSession, session_rows)

    print(
        f"Academic sessions: {session_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    term_rows = [
        {
            "id": UUID(raw["id"]),
            "academic_session_id": UUID(raw["academic_session_id"]),
            "term_type": AcademicTermType(raw["term_type"]),
            "working_days": raw.get("working_days"),
            "exam_result_date": parse_optional_date(
                raw.get("exam_result_date")
            ),
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in academic_terms
    ]
    term_inserted = insert_rows(AcademicTerm, term_rows)

    print(
        f"Academic terms: {term_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    class_rows = [
        {
            "id": UUID(raw["id"]),
            "academic_session_id": UUID(raw["academic_session_id"]),
            "grade": raw["grade"],
            "section": raw["section"],
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in academic_classes
    ]
    class_inserted = insert_rows(AcademicClass, class_rows)

    print(
        f"Academic classes: {class_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    subject_rows = [
        {
            "id": UUID(raw["id"]),
            "name": raw["name"],
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in subjects
    ]
    subject_inserted = insert_rows(Subject, subject_rows)

    print(
        f"Subjects: {subject_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    class_subject_rows = [
        {
            "id": UUID(raw["id"]),
            "academic_class_id": UUID(raw["academic_class_id"]),
            "subject_id": UUID(raw["subject_id"]),
            "is_additional": raw.get("is_additional", False),
            "position": raw["position"],
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in academic_class_subjects
    ]
    class_subject_inserted = insert_rows(
        AcademicClassSubject, class_subject_rows
    )

    print(
        f"Academic class subjects: {class_subject_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    class_subject_term_rows = [
        {
            "id": UUID(raw["id"]),
            "academic_class_subject_id": UUID(
                raw["academic_class_subject_id"]
            ),
            "academic_term_id": UUID(raw["academic_term_id"]),
            "highest_marks": raw.get("highest_marks"),
            "average_marks": raw.get("average_marks"),
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in academic_class_subject_terms
    ]
    class_subject_term_inserted = insert_rows(
        AcademicClassSubjectTerm, class_subject_term_rows
    )

    print(
        f"Academic class subject terms: {class_subject_term_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    student_rows = [
        {
            "id": UUID(raw["id"]),
            "registration_no": raw["registration_no"],
            "name": raw["name"],
            "dob": date.fromisoformat(raw["dob"]),
            "father_name": raw["father_name"],
            "mother_name": raw["mother_name"],
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in students
    ]
    student_inserted = insert_rows(Student, student_rows)

    print(
        f"Students: {student_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    enrollment_rows = [
        {
            "id": UUID(raw["id"]),
            "student_id": UUID(raw["student_id"]),
            "academic_session_id": UUID(raw["academic_session_id"]),
            "academic_class_id": UUID(raw["academic_class_id"]),
            "image": raw.get("image"),
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in enrollments
    ]
    enrollment_inserted = insert_rows(Enrollment, enrollment_rows)

    print(
        f"Enrollments: {enrollment_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    report_card_rows = [
        {
            "id": UUID(raw["id"]),
            "enrollment_id": UUID(raw["enrollment_id"]),
            "academic_term_id": UUID(raw["academic_term_id"]),
            "work_education_grade": ReportCardGrade(
                raw["work_education_grade"]
            )
            if raw.get("work_education_grade")
            else None,
            "art_education_grade": ReportCardGrade(
                raw["art_education_grade"]
            )
            if raw.get("art_education_grade")
            else None,
            "physical_education_grade": ReportCardGrade(
                raw["physical_education_grade"]
            )
            if raw.get("physical_education_grade")
            else None,
            "behaviour_grade": ReportCardGrade(raw["behaviour_grade"])
            if raw.get("behaviour_grade")
            else None,
            "attendance_present": raw.get("attendance_present"),
            "result": ReportCardResult(raw["result"])
            if raw.get("result")
            else None,
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in report_cards
    ]
    report_card_inserted = insert_rows(ReportCard, report_card_rows)

    print(
        f"Report cards: {report_card_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    report_card_subject_rows = [
        {
            "id": UUID(raw["id"]),
            "report_card_id": UUID(raw["report_card_id"]),
            "academic_class_subject_id": UUID(
                raw["academic_class_subject_id"]
            ),
            "mid_term": raw.get("mid_term"),
            "notebook": raw.get("notebook"),
            "assignment": raw.get("assignment"),
            "class_test": raw.get("class_test"),
            "final_term": raw.get("final_term"),
            "final_marks": raw.get("final_marks"),
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in report_card_subjects
    ]
    report_card_subject_inserted = insert_rows(
        ReportCardSubject, report_card_subject_rows
    )

    print(
        f"Report card subjects: {report_card_subject_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    date_sheet_rows = [
        {
            "id": UUID(raw["id"]),
            "academic_class_id": UUID(raw["academic_class_id"]),
            "academic_term_id": UUID(raw["academic_term_id"]),
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in date_sheets
    ]
    date_sheet_inserted = insert_rows(DateSheet, date_sheet_rows)

    print(
        f"Date sheets: {date_sheet_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    date_sheet_subject_rows = [
        {
            "id": UUID(raw["id"]),
            "date_sheet_id": UUID(raw["date_sheet_id"]),
            "academic_class_subject_id": UUID(
                raw["academic_class_subject_id"]
            ),
            "paper_code": raw.get("paper_code"),
            "exam_date": parse_optional_date(raw.get("exam_date")),
            "start_time": parse_optional_time(raw.get("start_time")),
            "end_time": parse_optional_time(raw.get("end_time")),
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in date_sheet_subjects
    ]
    date_sheet_subject_inserted = insert_rows(
        DateSheetSubject, date_sheet_subject_rows
    )

    print(
        f"Date sheet subjects: {date_sheet_subject_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    section_start = perf_counter()
    user_rows = [
        {
            "id": UUID(raw["id"]),
            "email": raw["email"],
            "role": UserRole(raw["role"]),
            "default_academic_session_id": UUID(
                raw["default_academic_session_id"]
            )
            if raw.get("default_academic_session_id")
            else None,
            "default_academic_term_id": UUID(raw["default_academic_term_id"])
            if raw.get("default_academic_term_id")
            else None,
            "default_academic_class_id": UUID(
                raw["default_academic_class_id"]
            )
            if raw.get("default_academic_class_id")
            else None,
            "created_at": parse_created_at(raw["created_at"]),
        }
        for raw in users
    ]
    user_inserted = insert_rows(User, user_rows)

    print(
        f"Users: {user_inserted} inserted "
        f"in {perf_counter() - section_start:.2f}s."
    )

    session.commit()
    print(f"Total seeding time: {perf_counter() - start_time:.2f}s.")


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
        session.info["db_namespace"] = normalize_db_namespace(
            os.getenv("DB_NAMESPACE")
        )
        seed_students(session, data_dir)
