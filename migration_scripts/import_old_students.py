from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

from sqlmodel import Session, select

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parents[0]
SRC_DIR = BASE_DIR / "src"
sys.path.append(str(SRC_DIR))

from db import engine  # noqa: E402
from models.academic_class import AcademicClass  # noqa: E402
from models.academic_session import AcademicSession  # noqa: E402
from models.academic_term import AcademicTerm  # noqa: E402
from models.date_sheet import DateSheet  # noqa: E402
from models.date_sheet_subject import DateSheetSubject  # noqa: E402
from models.enrollment import Enrollment  # noqa: E402
from models.report_card import ReportCard  # noqa: E402
from models.report_card_subject import ReportCardSubject  # noqa: E402
from models.student import Student  # noqa: E402

_ = [AcademicTerm, DateSheetSubject, ReportCardSubject, DateSheet, ReportCard]

DEFAULT_DOB = date(2000, 1, 1)
UNKNOWN_PARENT = "UNKNOWN"


def load_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def normalize(value: str | None) -> str:
    return value.strip() if value else ""


def normalize_key(value: str | None) -> str:
    return normalize(value).upper()


def get_or_create_academic_session(
    session: Session,
    raw_session: dict,
) -> AcademicSession:
    session_id = UUID(raw_session["id"])
    existing = session.get(AcademicSession, session_id)
    if existing:
        return existing

    statement = select(AcademicSession).where(
        AcademicSession.year == raw_session["year"],
    )
    existing = session.exec(statement).first()
    if existing:
        return existing

    created_at = parse_datetime(raw_session.get("created_at"))
    academic_session = AcademicSession(
        id=session_id,
        year=raw_session["year"],
        created_at=created_at or datetime.now(timezone.utc),
    )
    session.add(academic_session)
    session.commit()
    session.refresh(academic_session)
    return academic_session


def get_or_create_academic_class(
    session: Session,
    raw_class: dict,
) -> AcademicClass:
    class_id = UUID(raw_class["id"])
    existing = session.get(AcademicClass, class_id)
    if existing:
        return existing

    academic_session_id = UUID(raw_class["academic_session_id"])
    grade = normalize(raw_class.get("grade"))
    section = normalize(raw_class.get("section"))
    statement = select(AcademicClass).where(
        AcademicClass.academic_session_id == academic_session_id,
        AcademicClass.grade == grade,
        AcademicClass.section == section,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing

    created_at = parse_datetime(raw_class.get("created_at"))
    academic_class = AcademicClass(
        id=class_id,
        academic_session_id=academic_session_id,
        grade=grade,
        section=section,
        created_at=created_at or datetime.now(timezone.utc),
    )
    session.add(academic_class)
    session.commit()
    session.refresh(academic_class)
    return academic_class


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
        Student.registration_no == registration_no,
    )
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
    session.commit()
    session.refresh(student)
    return student, True


def get_or_create_enrollment(
    session: Session,
    student_id: UUID,
    academic_session_id: UUID,
    academic_class_id: UUID,
    image: str | None,
    created_at: datetime,
) -> tuple[Enrollment, bool]:
    statement = select(Enrollment).where(
        Enrollment.student_id == student_id,
        Enrollment.academic_session_id == academic_session_id,
    )
    existing = session.exec(statement).first()
    if existing:
        return existing, False

    enrollment = Enrollment(
        id=uuid4(),
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


def build_class_map(
    session: Session,
    raw_classes: list[dict],
) -> dict[tuple[str, str], UUID]:
    class_map: dict[tuple[str, str], UUID] = {}
    for raw_class in raw_classes:
        academic_class = get_or_create_academic_class(session, raw_class)
        class_id = UUID(raw_class["id"])
        key = (
            normalize_key(raw_class.get("grade")),
            normalize_key(raw_class.get("section")),
        )
        class_map[key] = class_id
    return class_map


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    data_path = base_dir / "data" / "old_students.json"
    classes_path = base_dir / "seeders" / "data" / \
        "old_data" / "academic_classes.json"
    sessions_path = (
        base_dir / "seeders" / "data" / "old_data" / "academic_sessions.json"
    )

    students = load_json(data_path)
    raw_classes = load_json(classes_path)
    raw_sessions = load_json(sessions_path)

    if not raw_sessions:
        raise ValueError("No academic sessions found in old data.")

    target_session = raw_sessions[0]
    target_session_id = UUID(target_session["id"])

    stats = {
        "students_created": 0,
        "students_existing": 0,
        "students_skipped": 0,
        "enrollments_created": 0,
        "enrollments_existing": 0,
        "enrollments_skipped": 0,
        "missing_class_map": 0,
    }

    with Session(engine) as session:
        get_or_create_academic_session(session, target_session)
        class_map = build_class_map(session, raw_classes)

        for item in students:
            raw_value = item.get("value") or {}
            student_id_raw = raw_value.get("id")
            if not student_id_raw:
                stats["students_skipped"] += 1
                stats["enrollments_skipped"] += 1
                continue

            try:
                student_id = UUID(student_id_raw)
            except ValueError:
                stats["students_skipped"] += 1
                stats["enrollments_skipped"] += 1
                continue

            registration_no = normalize(raw_value.get("Regn. No."))
            name = normalize(raw_value.get("Student Name"))
            if not registration_no or not name:
                stats["students_skipped"] += 1
                stats["enrollments_skipped"] += 1
                continue

            class_key = (
                normalize_key(raw_value.get("Class")),
                normalize_key(raw_value.get("Section")),
            )
            academic_class_id = class_map.get(class_key)
            if not academic_class_id:
                stats["missing_class_map"] += 1
                stats["students_skipped"] += 1
                stats["enrollments_skipped"] += 1
                continue

            dob = parse_date(raw_value.get("Date of Birth")) or DEFAULT_DOB
            father_name = (
                normalize(raw_value.get("Father's Name")) or UNKNOWN_PARENT
            )
            mother_name = (
                normalize(raw_value.get("Mother's Name")) or UNKNOWN_PARENT
            )
            created_at = parse_datetime(item.get("createdAt")) or datetime.now(
                timezone.utc
            )

            student, student_created = get_or_create_student(
                session=session,
                student_id=student_id,
                registration_no=registration_no,
                name=name,
                dob=dob,
                father_name=father_name,
                mother_name=mother_name,
                created_at=created_at,
            )

            if student_created:
                stats["students_created"] += 1
            else:
                stats["students_existing"] += 1

            image = raw_value.get("studentImage")
            _, enrollment_created = get_or_create_enrollment(
                session=session,
                student_id=student_id,
                academic_session_id=target_session_id,
                academic_class_id=academic_class_id,
                image=image,
                created_at=created_at,
            )
            if enrollment_created:
                stats["enrollments_created"] += 1
            else:
                stats["enrollments_existing"] += 1

    print(
        "Created students: {students_created}, existing: {students_existing}, "
        "skipped: {students_skipped}; enrollments created: {enrollments_created}, "
        "existing: {enrollments_existing}, skipped: {enrollments_skipped}; "
        "missing class mapping: {missing_class_map}".format(**stats)
    )


if __name__ == "__main__":
    main()
