import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, SQLModel, col, select

from db import get_session
from models.academic_class import AcademicClass, AcademicClassRead
from models.academic_class_subject import AcademicClassSubject
from models.academic_session import AcademicSession, AcademicSessionRead
from models.academic_term import (AcademicTerm, AcademicTermRead,
                                  AcademicTermType)
from models.date_sheet import DateSheet, DateSheetRead, DateSheetReadDetail
from models.date_sheet_subject import DateSheetSubjectRead
from models.enrollment import Enrollment, EnrollmentRead
from models.report_card import (ReportCard, ReportCardReadDetail,
                                ReportCardReadDetailWithSubjects)
from models.report_card_subject import ReportCardSubject, ReportCardSubjectRead
from models.student import Student
from routers.academic_classes import grade_rank
from routers.academic_terms import term_rank
from routers.date_sheets import query_date_sheet_subjects
from routers.report_card_subjects import REPORT_CARD_SUBJECT_ORDER_BY
from routers.report_cards import populate_rank_and_percentage

router = APIRouter(
    prefix="/public",
    tags=["public"],
)


class AdmitCardDataResponse(SQLModel):
    enrollment: EnrollmentRead
    academic_term: AcademicTermRead
    date_sheet: DateSheetReadDetail | None = None


class ReportCardDataResponse(SQLModel):
    report_card: ReportCardReadDetailWithSubjects
    half_yearly_report_card: ReportCardReadDetailWithSubjects | None = None


def _query_report_card_subjects(
    session: Session,
    report_card_id: UUID,
) -> list[ReportCardSubjectRead]:
    results = session.exec(
        select(ReportCardSubject)
        .join(
            AcademicClassSubject,
            col(AcademicClassSubject.id)
            == col(ReportCardSubject.academic_class_subject_id),
        )
        .where(ReportCardSubject.report_card_id == report_card_id)
        .order_by(*REPORT_CARD_SUBJECT_ORDER_BY)
    ).all()
    return [
        ReportCardSubjectRead.model_validate(item)
        for item in results
    ]


def _compute_totals_by_report_card(
    session: Session,
    report_card_ids: list[UUID],
) -> dict[UUID, tuple[int, int]]:
    if not report_card_ids:
        return {}

    subject_total = (
        func.coalesce(ReportCardSubject.notebook, 0)
        + func.coalesce(ReportCardSubject.class_test, 0)
        + func.coalesce(ReportCardSubject.assignment, 0)
        + func.coalesce(ReportCardSubject.mid_term, 0)
        + func.coalesce(ReportCardSubject.final_term, 0)
    )

    totals = session.exec(
        select(
            col(ReportCardSubject.report_card_id),
            func.coalesce(func.sum(subject_total), 0),
            func.count(col(ReportCardSubject.id)),
        )
        .join(
            AcademicClassSubject,
            col(AcademicClassSubject.id)
            == col(ReportCardSubject.academic_class_subject_id),
        )
        .where(
            col(ReportCardSubject.report_card_id).in_(report_card_ids),
            col(AcademicClassSubject.is_additional) == False,
        )
        .group_by(col(ReportCardSubject.report_card_id))
    ).all()

    totals_by_id: dict[UUID, tuple[int, int]] = {}
    for report_card_id, total_marks, subject_count in totals:
        totals_by_id[report_card_id] = (total_marks, subject_count)
    return totals_by_id


def _compute_percentages_and_ranks(
    totals_by_id: dict[UUID, tuple[int, int]]
) -> tuple[dict[UUID, int], dict[UUID, int]]:
    percentages_by_id: dict[UUID, int] = {}
    for report_card_id, (total_marks,
                         subject_count) in totals_by_id.items():
        if subject_count:
            percentages_by_id[report_card_id] = math.ceil(
                total_marks / subject_count
            )

    ranks_by_id: dict[UUID, int] = {}
    sorted_items = sorted(
        percentages_by_id.items(), key=lambda item: item[1], reverse=True
    )
    current_rank = 0
    last_percentage = None
    for index, (report_card_id, percentage) in enumerate(
        sorted_items, start=1
    ):
        if percentage != last_percentage:
            current_rank = index
            last_percentage = percentage
        ranks_by_id[report_card_id] = current_rank

    return percentages_by_id, ranks_by_id


@router.get("/report-card-data", response_model=ReportCardDataResponse)
def get_report_card(
    student_registration_no: str = Query(...),
    academic_term_id: UUID = Query(...),
    session: Session = Depends(get_session),
):
    academic_term = session.get(AcademicTerm, academic_term_id)
    if not academic_term:
        raise HTTPException(
            status_code=404, detail="Academic term not found"
        )

    student = session.exec(
        select(Student).where(
            Student.registration_no == student_registration_no,
        )
    ).first()
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found for the provided registration number",
        )

    enrollment = session.exec(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.academic_session_id
            == academic_term.academic_session_id,
        )
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found for the selected session",
        )

    report_card = session.exec(
        select(ReportCard).where(
            ReportCard.academic_term_id == academic_term_id,
            ReportCard.enrollment_id == enrollment.id,
        )
    ).first()
    read_report_card = ReportCardReadDetail.model_validate(report_card)
    half_yearly_report_card_read: ReportCardReadDetail | None = None
    half_yearly_report_card_with_subjects = None
    if academic_term.term_type == AcademicTermType.ANNUAL:
        half_yearly_term = session.exec(
            select(AcademicTerm).where(
                AcademicTerm.academic_session_id
                == academic_term.academic_session_id,
                AcademicTerm.term_type == AcademicTermType.HALF_YEARLY,
            )
        ).first()
        if half_yearly_term:
            half_yearly_report_card = session.exec(
                select(ReportCard).where(
                    ReportCard.academic_term_id == half_yearly_term.id,
                    ReportCard.enrollment_id == enrollment.id,
                )
            ).first()
            if half_yearly_report_card:
                half_yearly_report_card_read = (
                    ReportCardReadDetail.model_validate(
                        half_yearly_report_card
                    )
                )
                populate_rank_and_percentage(
                    half_yearly_report_card_read, session
                )
                half_yearly_report_card_with_subjects = (
                    ReportCardReadDetailWithSubjects(
                        **half_yearly_report_card_read.model_dump(),
                        report_card_subjects=_query_report_card_subjects(
                            session, half_yearly_report_card_read.id
                        ),
                    )
                )

        annual_report_cards_raw = session.exec(
            select(ReportCard.id, ReportCard.enrollment_id)
            .join(Enrollment)
            .where(
                Enrollment.academic_class_id
                == enrollment.academic_class_id,
                ReportCard.academic_term_id == academic_term_id,
            )
        ).all()
        annual_report_cards = [
            (report_card_id, enrollment_id)
            for report_card_id, enrollment_id in annual_report_cards_raw
            if report_card_id is not None and enrollment_id is not None
        ]
        annual_report_card_ids = [
            report_card_id for report_card_id, _ in annual_report_cards
        ]
        annual_totals_by_id = _compute_totals_by_report_card(
            session, annual_report_card_ids
        )

        half_yearly_report_card_ids_by_enrollment: dict[
            UUID, UUID
        ] = {}
        if half_yearly_term:
            enrollment_ids = [
                enrollment_id for _, enrollment_id in annual_report_cards
            ]
            half_yearly_report_cards_raw = session.exec(
                select(ReportCard.id, ReportCard.enrollment_id).where(
                    ReportCard.academic_term_id == half_yearly_term.id,
                    col(ReportCard.enrollment_id).in_(enrollment_ids),
                )
            ).all()
            half_yearly_report_card_ids_by_enrollment = {
                enrollment_id: report_card_id
                for report_card_id, enrollment_id
                in half_yearly_report_cards_raw
                if report_card_id is not None
                and enrollment_id is not None
            }

        half_yearly_totals_by_id = _compute_totals_by_report_card(
            session, list(half_yearly_report_card_ids_by_enrollment.values())
        )
        combined_totals_by_id: dict[UUID, tuple[int, int]] = {}
        for annual_report_card_id, enrollment_id in annual_report_cards:
            annual_total, annual_count = annual_totals_by_id.get(
                annual_report_card_id, (0, 0)
            )
            half_yearly_report_card_id = (
                half_yearly_report_card_ids_by_enrollment.get(enrollment_id)
            )
            half_yearly_total, half_yearly_count = (
                half_yearly_totals_by_id.get(
                    half_yearly_report_card_id, (0, 0)
                )
                if half_yearly_report_card_id
                else (0, 0)
            )
            total_marks = annual_total + half_yearly_total
            subject_count = annual_count + half_yearly_count
            if subject_count:
                combined_totals_by_id[annual_report_card_id] = (
                    total_marks,
                    subject_count,
                )
        combined_percentages, combined_ranks = (
            _compute_percentages_and_ranks(combined_totals_by_id)
        )
        if read_report_card.id in combined_percentages:
            read_report_card.overall_percentage = combined_percentages[
                read_report_card.id
            ]
            read_report_card.rank = combined_ranks.get(read_report_card.id)
    else:
        populate_rank_and_percentage(read_report_card, session)

    report_card_subjects = _query_report_card_subjects(
        session, read_report_card.id
    )
    rc_with_subjects = ReportCardReadDetailWithSubjects(
        **read_report_card.model_dump(),
        report_card_subjects=report_card_subjects,
    )
    return ReportCardDataResponse(
        report_card=rc_with_subjects,
        half_yearly_report_card=half_yearly_report_card_with_subjects,
    )


@router.get("/admit-card-data", response_model=AdmitCardDataResponse)
def get_admit_card(
    student_registration_no: str = Query(...),
    academic_term_id: UUID = Query(...),
    session: Session = Depends(get_session),
):
    academic_term = session.get(AcademicTerm, academic_term_id)
    if not academic_term:
        raise HTTPException(
            status_code=404, detail="Academic term not found"
        )

    student = session.exec(
        select(Student).where(
            Student.registration_no == student_registration_no,
        )
    ).first()
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found for the provided registration number",
        )

    enrollment = session.exec(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.academic_session_id
            == academic_term.academic_session_id,
        )
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found for the selected session",
        )

    date_sheet = session.exec(
        select(DateSheet).where(
            DateSheet.academic_class_id == enrollment.academic_class_id,
            DateSheet.academic_term_id == academic_term_id,
        )
    ).first()

    date_sheet_subjects: list[DateSheetSubjectRead] = []
    if date_sheet and date_sheet.id:
        date_sheet_subjects = query_date_sheet_subjects(
            session, date_sheet.id
        )

    date_sheet_read: DateSheetReadDetail | None = None
    if date_sheet:
        date_sheet_base = DateSheetRead.model_validate(date_sheet)
        date_sheet_read = DateSheetReadDetail(
            **date_sheet_base.model_dump(),
            date_sheet_subjects=date_sheet_subjects,
        )

    return AdmitCardDataResponse(
        enrollment=EnrollmentRead.model_validate(enrollment),
        academic_term=AcademicTermRead.model_validate(academic_term),
        date_sheet=date_sheet_read,
    )


class IdCardDataResponse(SQLModel):
    enrollment: EnrollmentRead


@router.get("/id-card-data", response_model=IdCardDataResponse)
def get_id_card_data(
    student_registration_no: str = Query(...),
    academic_session_id: UUID = Query(...),
    session: Session = Depends(get_session),
):
    student = session.exec(
        select(Student).where(
            Student.registration_no == student_registration_no,
        )
    ).first()
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found for the provided registration number",
        )

    enrollment = session.exec(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.academic_session_id == academic_session_id,
        )
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=404,
            detail="Enrollment not found for the given session",
        )

    return IdCardDataResponse(enrollment=EnrollmentRead.model_validate(enrollment))


class DateSheetDataResponse(SQLModel):
    date_sheet: DateSheetReadDetail


@router.get("/date-sheet-data", response_model=DateSheetDataResponse)
def get_date_sheet_data(
    academic_class_id: UUID = Query(...),
    academic_term_id: UUID = Query(...),
    session: Session = Depends(get_session),
):
    date_sheet = session.exec(
        select(DateSheet).where(
            DateSheet.academic_class_id == academic_class_id,
            DateSheet.academic_term_id == academic_term_id,
        )
    ).first()
    if not date_sheet:
        raise HTTPException(
            status_code=404,
            detail="Date sheet not found for the provided class and term",
        )

    date_sheet_subjects: list[DateSheetSubjectRead] = []
    if date_sheet.id:
        date_sheet_subjects = query_date_sheet_subjects(
            session, date_sheet.id
        )

    date_sheet_base = DateSheetRead.model_validate(date_sheet)
    date_sheet_read = DateSheetReadDetail(
        **date_sheet_base.model_dump(),
        date_sheet_subjects=date_sheet_subjects,
    )
    return DateSheetDataResponse(date_sheet=date_sheet_read)


@router.get("/academic-sessions", response_model=list[AcademicSessionRead])
def get_academic_sessions(
    session: Session = Depends(get_session),
):
    statement = select(AcademicSession)
    results = session.exec(
        statement.order_by(
            col(AcademicSession.year),
            col(AcademicSession.created_at).desc(),
        )
    ).all()
    return results


@router.get("/academic-terms", response_model=list[AcademicTermRead])
def get_academic_terms(
    academic_session_id: UUID = Query(),
    session: Session = Depends(get_session),
):
    statement = select(AcademicTerm).where(
        AcademicTerm.academic_session_id == academic_session_id)
    results = session.exec(
        statement.order_by(
            term_rank,
            col(AcademicTerm.created_at).desc(),
        )
    ).all()
    return results


@router.get("/academic-classes", response_model=list[AcademicClassRead])
def get_academic_classes(
    academic_session_id: UUID = Query(),
    session: Session = Depends(get_session),
):
    statement = select(AcademicClass).where(
        AcademicClass.academic_session_id == academic_session_id)
    results = session.exec(
        statement.order_by(
            grade_rank,
            col(AcademicClass.section),
            col(AcademicClass.created_at).desc(),
        )
    ).all()
    return results
