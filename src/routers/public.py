from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
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
from models.gk_competition_student import (GKCompetitionStudent,
                                           GKCompetitionStudentRead)
from models.report_card import (ReportCard, ReportCardReadDetail,
                                ReportCardReadDetailWithSubjects)
from models.report_card_subject import ReportCardSubject, ReportCardSubjectRead
from models.student import Student
from routers.academic_classes import grade_rank
from routers.academic_terms import term_rank
from routers.app_settings import _get_or_create_settings
from routers.date_sheets import query_date_sheet_subjects
from routers.report_card_subjects import REPORT_CARD_SUBJECT_ORDER_BY
from routers.report_cards import (compute_percentages_and_ranks_for_term,
                                  populate_rank_and_percentage)

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

        combined_percentages, combined_ranks = (
            compute_percentages_and_ranks_for_term(
                session,
                academic_term,
                enrollment.academic_class_id,
            )
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


class GKCompetitionStudentDataResponse(SQLModel):
    gk_competition_student: GKCompetitionStudentRead


class SettingsDataResponse(SQLModel):
    gk_competition_result_active: bool


@router.get(
    "/gk-competition-student-data",
    response_model=GKCompetitionStudentDataResponse,
)
def get_gk_competition_student_data(
    aadhaar_no: str = Query(...),
    roll_no: str = Query(...),
    session: Session = Depends(get_session),
):

    student = session.exec(
        select(GKCompetitionStudent).where(
            col(GKCompetitionStudent.aadhaar_no) == aadhaar_no,
            col(GKCompetitionStudent.roll_no) == roll_no,
        )
    ).first()
    if not student:
        err_message = "Roll Number or Aadhaar Number does not match our records. Please check and try again."
        raise HTTPException(
            status_code=404, detail=err_message
        )
    return GKCompetitionStudentDataResponse(
        gk_competition_student=GKCompetitionStudentRead.model_validate(
            student
        )
    )


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


@router.get("/settings-data", response_model=SettingsDataResponse)
def get_settings_data(
    session: Session = Depends(get_session),
):
    settings = _get_or_create_settings(session)
    return SettingsDataResponse(
        gk_competition_result_active=settings.gk_competition_result_active
    )


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
