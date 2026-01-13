from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, SQLModel, col, select

from db import get_session
from models.academic_class import AcademicClass, AcademicClassRead
from models.academic_class_subject import AcademicClassSubject
from models.academic_session import AcademicSession, AcademicSessionRead
from models.academic_term import AcademicTerm, AcademicTermRead
from models.date_sheet import DateSheet, DateSheetReadDetail
from models.date_sheet_subject import DateSheetSubject, DateSheetSubjectRead
from models.enrollment import Enrollment, EnrollmentRead
from models.report_card import ReportCard, ReportCardReadDetail
from models.report_card_subject import ReportCardSubject, ReportCardSubjectRead
from models.student import Student
from routers.academic_classes import grade_rank
from routers.academic_terms import term_rank
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


def _query_date_sheet_subjects(
    session: Session, date_sheet_id: UUID
) -> list[DateSheetSubjectRead]:
    results = session.exec(
        select(DateSheetSubject)
        .join(
            AcademicClassSubject,
            col(AcademicClassSubject.id)
            == col(DateSheetSubject.academic_class_subject_id),
        )
        .where(DateSheetSubject.date_sheet_id == date_sheet_id)
        .order_by(
            col(DateSheetSubject.exam_date).asc().nulls_last(),
            col(DateSheetSubject.start_time).asc().nulls_last(),
            col(DateSheetSubject.end_time).asc().nulls_last(),
            col(AcademicClassSubject.is_additional).asc(),
            col(AcademicClassSubject.position).asc(),
            col(DateSheetSubject.created_at).desc(),
        )
    ).all()
    return [
        DateSheetSubjectRead.model_validate(item)
        for item in results
    ]


class ReportCardDataResponse(SQLModel):
    report_card: ReportCardReadDetail


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
    populate_rank_and_percentage(read_report_card, session)
    results = session.exec(
        select(ReportCardSubject)
        .join(
            AcademicClassSubject,
            col(AcademicClassSubject.id)
            == col(ReportCardSubject.academic_class_subject_id),
        )
        .where(ReportCardSubject.report_card_id == read_report_card.id)
        .order_by(*REPORT_CARD_SUBJECT_ORDER_BY)
    ).all()
    report_card_subjects = [
        ReportCardSubjectRead.model_validate(item)
        for item in results
    ]
    read_report_card.report_card_subjects = report_card_subjects
    return ReportCardDataResponse(
        report_card=read_report_card,
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
        date_sheet_subjects = _query_date_sheet_subjects(
            session, date_sheet.id
        )

    date_sheet_read: DateSheetReadDetail | None = None
    if date_sheet:
        date_sheet_read = DateSheetReadDetail.model_validate(date_sheet)
        date_sheet_read.date_sheet_subjects = date_sheet_subjects

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
        date_sheet_subjects = _query_date_sheet_subjects(
            session, date_sheet.id
        )

    date_sheet_read = DateSheetReadDetail.model_validate(date_sheet)
    date_sheet_read.date_sheet_subjects = date_sheet_subjects
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
