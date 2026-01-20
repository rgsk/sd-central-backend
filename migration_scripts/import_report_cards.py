from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID

from sqlmodel import Session, select

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_DIR = SCRIPT_DIR.parents[0]
SRC_DIR = BASE_DIR / "src"
sys.path.append(str(SRC_DIR))

from db import engine  # noqa: E402
from models.academic_class_subject import AcademicClassSubject  # noqa: E402
from models.academic_session import AcademicSession  # noqa: E402
from models.academic_term import AcademicTerm  # noqa: E402
from models.academic_term import AcademicTermType  # noqa: E402
from models.date_sheet import DateSheet  # noqa: E402
from models.date_sheet_subject import DateSheetSubject  # noqa: E402
from models.enrollment import Enrollment  # noqa: E402
from models.report_card import ReportCard  # noqa: E402
from models.report_card import ReportCardGrade, ReportCardResult  # noqa: E402
from models.report_card_subject import ReportCardSubject  # noqa: E402
from models.subject import Subject  # noqa: E402

_ = [AcademicTerm, DateSheetSubject, ReportCardSubject, DateSheet, ReportCard]

SESSION_YEAR = "2025-2026"

QUARTERLY_DATA = "data/exam_marks_2025-2026_quarterly.json"
HALF_YEARLY_DATA = "data/exam_marks_2025-2026_half-yearly.json"

SPECIAL_KEYS = {"ATTENDANCE", "GRADING SCALES", "REPORT DETAILS"}

ALIAS_SUBJECTS: dict[str, list[str]] = {
    "GENERAL KNOWLEDGE": ["GK"],
    "GK": ["GENERAL KNOWLEDGE"],
    "MATH": ["MATHEMATICS"],
    "MATHS": ["MATHEMATICS"],
    "MATHEMATICS": ["MATH", "MATHS"],
    "SOCAIL SCIENCE": ["SOCIAL SCIENCE"],
    "SOCAIL SCENCE": ["SOCIAL SCIENCE"],
    "SOCIAL SCIOENCE": ["SOCIAL SCIENCE"],
    "SOCIAL SCIENCE": ["SOCAIL SCIENCE", "SOCIAL SCIOENCE", "SOCAIL SCENCE"],
    "DRAWIBNG": ["DRAWING"],
    "DRAWING54": ["DRAWING"],
}

COMPONENT_MAP = {
    "mid_term": "mid_term",
    "midterm": "mid_term",
    "notebook": "notebook",
    "assignment": "assignment",
    "class_test": "class_test",
    "classtest": "class_test",
    "final_term": "final_term",
    "finalterm": "final_term",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            return int(float(cleaned))
        except ValueError:
            return None
    return None


def normalize_subject(value: str | None) -> str:
    if not value:
        return ""
    cleaned = re.sub(r"\s+", " ", value.strip())
    return cleaned.upper()


def normalize_component(value: str | None) -> str:
    if not value:
        return ""
    cleaned = value.strip().lower().replace("-", " ")
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned


def candidate_subject_names(normalized: str) -> list[str]:
    candidates = [normalized]
    candidates.extend(ALIAS_SUBJECTS.get(normalized, []))
    trimmed = re.sub(r"\d+$", "", normalized)
    if trimmed and trimmed != normalized:
        candidates.append(trimmed)
        candidates.extend(ALIAS_SUBJECTS.get(trimmed, []))
    return list(dict.fromkeys(candidates))


def get_academic_session(session: Session, year: str) -> AcademicSession:
    statement = select(AcademicSession).where(AcademicSession.year == year)
    existing = session.exec(statement).first()
    if not existing:
        raise ValueError(f"Academic session for {year} not found.")
    return existing


def get_academic_term(
    session: Session,
    academic_session_id: UUID,
    term_type: AcademicTermType,
) -> AcademicTerm:
    statement = select(AcademicTerm).where(
        AcademicTerm.academic_session_id == academic_session_id,
        AcademicTerm.term_type == term_type,
    )
    existing = session.exec(statement).first()
    if not existing:
        raise ValueError(
            f"Academic term {term_type.value} for session not found."
        )
    return existing


def build_enrollment_map(
    session: Session,
    academic_session_id: UUID,
) -> dict[UUID, tuple[UUID, UUID]]:
    rows = session.exec(
        select(Enrollment.id, Enrollment.student_id,
               Enrollment.academic_class_id)
        .where(Enrollment.academic_session_id == academic_session_id)
    ).all()
    enrollment_map: dict[UUID, tuple[UUID, UUID]] = {}
    for enrollment_id, student_id, class_id in rows:
        if enrollment_id and student_id and class_id:
            enrollment_map[student_id] = (enrollment_id, class_id)
    return enrollment_map


def build_class_subject_map(
    session: Session,
    academic_term_id: UUID,
) -> dict[UUID, dict[str, UUID]]:
    rows = session.exec(
        select(
            AcademicClassSubject.id,
            AcademicClassSubject.academic_class_id,
            Subject.name,
        )
        .join(Subject)
        .where(AcademicClassSubject.academic_term_id == academic_term_id)
    ).all()
    class_subjects: dict[UUID, dict[str, UUID]] = {}
    for class_subject_id, class_id, subject_name in rows:
        if not class_subject_id or not class_id or not subject_name:
            continue
        normalized = normalize_subject(subject_name)
        class_subjects.setdefault(class_id, {})[normalized] = class_subject_id
    return class_subjects


def get_or_create_report_card(
    session: Session,
    report_cards_by_enrollment: dict[UUID, ReportCard],
    enrollment_id: UUID,
    academic_term_id: UUID,
) -> tuple[ReportCard, bool]:
    existing = report_cards_by_enrollment.get(enrollment_id)
    if existing:
        return existing, False
    report_card = ReportCard(
        enrollment_id=enrollment_id,
        academic_term_id=academic_term_id,
    )
    session.add(report_card)
    session.flush()
    report_cards_by_enrollment[enrollment_id] = report_card
    return report_card, True


def parse_grade(value: Any) -> ReportCardGrade | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    if normalized in ReportCardGrade.__members__:
        return ReportCardGrade[normalized]
    return None


def parse_result(value: Any) -> ReportCardResult | None:
    if not isinstance(value, str):
        return None
    normalized = re.sub(r"\s+", "_", value.strip().lower())
    mapping = {
        "promoted": ReportCardResult.PROMOTED,
        "passed": ReportCardResult.PASSED,
        "pass": ReportCardResult.PASSED,
        "need_improvement": ReportCardResult.NEED_IMPROVEMENT,
        "result_withheld": ReportCardResult.RESULT_WITHHELD,
        "result_withhelds": ReportCardResult.RESULT_WITHHELD,
    }
    return mapping.get(normalized)


def apply_report_card_metadata(report_card: ReportCard, record: dict[str, Any]) -> bool:
    changed = False
    attendance = record.get("Attendance")
    if isinstance(attendance, dict):
        present = parse_int(attendance.get("Present"))
        if present is not None and report_card.attendance_present != present:
            report_card.attendance_present = present
            changed = True

    grading_scales = record.get("Grading Scales")
    if isinstance(grading_scales, dict):
        behaviour = parse_grade(grading_scales.get("Behaviour"))
        if behaviour and report_card.behaviour_grade != behaviour:
            report_card.behaviour_grade = behaviour
            changed = True
        art = parse_grade(grading_scales.get("Art Education"))
        if art and report_card.art_education_grade != art:
            report_card.art_education_grade = art
            changed = True
        work = parse_grade(grading_scales.get("Work Education"))
        if work and report_card.work_education_grade != work:
            report_card.work_education_grade = work
            changed = True
        physical = parse_grade(grading_scales.get("Physical Education"))
        if physical and report_card.physical_education_grade != physical:
            report_card.physical_education_grade = physical
            changed = True

    report_details = record.get("Report Details")
    if isinstance(report_details, dict):
        result = parse_result(report_details.get("Result"))
        if result and report_card.result != result:
            report_card.result = result
            changed = True

    return changed


def get_report_card_subject_map(
    session: Session,
    cache: dict[UUID, dict[UUID, ReportCardSubject]],
    report_card_id: UUID,
) -> dict[UUID, ReportCardSubject]:
    if report_card_id in cache:
        return cache[report_card_id]
    rows = session.exec(
        select(ReportCardSubject).where(
            ReportCardSubject.report_card_id == report_card_id
        )
    ).all()
    subject_map = {
        row.academic_class_subject_id: row
        for row in rows
        if row.academic_class_subject_id
    }
    cache[report_card_id] = subject_map
    return subject_map


SubjectField = Literal[
    "mid_term",
    "notebook",
    "assignment",
    "class_test",
    "final_term",
    "final_marks",
]


def build_subject_fields(value: Any) -> dict[SubjectField, int | None]:
    if isinstance(value, dict):
        fields: dict[SubjectField, int | None] = {}
        for key, raw in value.items():
            normalized = normalize_component(key)
            field_name = COMPONENT_MAP.get(normalized)
            if field_name:
                typed_name = cast(SubjectField, field_name)
                fields[typed_name] = parse_int(raw)
        return fields
    return {"final_marks": parse_int(value)}


def find_class_subject_id(
    class_subjects: dict[UUID, dict[str, UUID]],
    class_id: UUID,
    raw_subject: str,
) -> UUID | None:
    normalized = normalize_subject(raw_subject)
    subject_map = class_subjects.get(class_id, {})
    for candidate in candidate_subject_names(normalized):
        matched = subject_map.get(candidate)
        if matched:
            return matched
    return None


def process_term(
    session: Session,
    academic_session_id: UUID,
    term_type: AcademicTermType,
    data_path: Path,
    enrollment_map: dict[UUID, tuple[UUID, UUID]],
) -> dict[str, int]:
    data = load_json(data_path)
    records = data.get("records")
    if not isinstance(records, dict):
        raise ValueError(f"Invalid records in {data_path}.")

    academic_term = get_academic_term(session, academic_session_id, term_type)
    academic_term_id = academic_term.id
    if academic_term_id is None:
        raise ValueError(
            f"Academic term {term_type.value} has no ID."
        )
    class_subjects = build_class_subject_map(session, academic_term_id)

    report_cards_by_enrollment: dict[UUID, ReportCard] = {}
    existing_cards = session.exec(
        select(ReportCard).where(
            ReportCard.academic_term_id == academic_term_id)
    ).all()
    for report_card in existing_cards:
        report_cards_by_enrollment[report_card.enrollment_id] = report_card

    subject_cache: dict[UUID, dict[UUID, ReportCardSubject]] = {}
    stats = {
        "report_cards_created": 0,
        "report_cards_existing": 0,
        "report_cards_skipped": 0,
        "report_card_subjects_created": 0,
        "report_card_subjects_updated": 0,
        "report_card_subjects_skipped": 0,
        "missing_enrollment": 0,
        "missing_subject": 0,
    }

    for student_id_raw, record in records.items():
        try:
            student_id = UUID(student_id_raw)
        except ValueError:
            stats["report_cards_skipped"] += 1
            continue

        if not isinstance(record, dict):
            stats["report_cards_skipped"] += 1
            continue

        enrollment = enrollment_map.get(student_id)
        if not enrollment:
            stats["missing_enrollment"] += 1
            stats["report_cards_skipped"] += 1
            continue

        enrollment_id, class_id = enrollment
        report_card, created = get_or_create_report_card(
            session=session,
            report_cards_by_enrollment=report_cards_by_enrollment,
            enrollment_id=enrollment_id,
            academic_term_id=academic_term_id,
        )
        if report_card.id is None:
            raise ValueError(
                f"Report card ID missing for enrollment {enrollment_id}."
            )
        if created:
            stats["report_cards_created"] += 1
        else:
            stats["report_cards_existing"] += 1

        updated_metadata = False
        if term_type == AcademicTermType.HALF_YEARLY:
            updated_metadata = apply_report_card_metadata(report_card, record)

        subject_map = get_report_card_subject_map(
            session, subject_cache, report_card.id
        )
        for raw_subject, raw_value in record.items():
            if normalize_subject(raw_subject) in SPECIAL_KEYS:
                continue
            class_subject_id = find_class_subject_id(
                class_subjects,
                class_id,
                raw_subject,
            )
            if not class_subject_id:
                stats["missing_subject"] += 1
                stats["report_card_subjects_skipped"] += 1
                continue

            fields = build_subject_fields(raw_value)
            existing_subject = subject_map.get(class_subject_id)
            if existing_subject:
                changed = False
                for field_name, field_value in fields.items():
                    if getattr(existing_subject, field_name) != field_value:
                        setattr(existing_subject, field_name, field_value)
                        changed = True
                if changed:
                    stats["report_card_subjects_updated"] += 1
                continue

            report_card_subject = ReportCardSubject(
                report_card_id=report_card.id,
                academic_class_subject_id=class_subject_id,
                **fields,
            )
            session.add(report_card_subject)
            subject_map[class_subject_id] = report_card_subject
            stats["report_card_subjects_created"] += 1

        if created or updated_metadata:
            report_card.created_at = report_card.created_at or datetime.now(
                timezone.utc
            )
        session.commit()

    return stats


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    quarterly_path = base_dir / QUARTERLY_DATA
    half_yearly_path = base_dir / HALF_YEARLY_DATA

    with Session(engine) as session:
        academic_session = get_academic_session(session, SESSION_YEAR)
        academic_session_id = academic_session.id
        if academic_session_id is None:
            raise ValueError(
                f"Academic session {SESSION_YEAR} has no ID."
            )
        enrollment_map = build_enrollment_map(
            session, academic_session_id
        )

        quarterly_stats = process_term(
            session=session,
            academic_session_id=academic_session_id,
            term_type=AcademicTermType.QUARTERLY,
            data_path=quarterly_path,
            enrollment_map=enrollment_map,
        )
        half_yearly_stats = process_term(
            session=session,
            academic_session_id=academic_session_id,
            term_type=AcademicTermType.HALF_YEARLY,
            data_path=half_yearly_path,
            enrollment_map=enrollment_map,
        )

    print("Quarterly stats:", quarterly_stats)
    print("Half-yearly stats:", half_yearly_stats)


if __name__ == "__main__":
    main()
