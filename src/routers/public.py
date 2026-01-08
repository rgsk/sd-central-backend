from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class_subject import AcademicClassSubject
from models.academic_term import AcademicTerm, AcademicTermRead
from models.admit_card import AdmitCardResponse
from models.datesheet import DateSheet
from models.datesheet_subject import DateSheetSubject, DateSheetSubjectRead
from models.enrollment import Enrollment, EnrollmentRead

router = APIRouter(
    prefix="/public",
    tags=["public"],
)


@router.get("/admit-card", response_model=AdmitCardResponse)
def get_admit_card(
    enrollment_id: UUID = Query(...),
    academic_term_id: UUID = Query(...),
    session: Session = Depends(get_session),
):
    enrollment = session.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=404, detail="Enrollment not found"
        )

    academic_term = session.get(AcademicTerm, academic_term_id)
    if not academic_term:
        raise HTTPException(
            status_code=404, detail="Academic term not found"
        )

    if enrollment.academic_session_id != academic_term.academic_session_id:
        raise HTTPException(
            status_code=400,
            detail="Academic term does not match enrollment session",
        )

    date_sheet = session.exec(
        select(DateSheet).where(
            DateSheet.academic_class_id == enrollment.academic_class_id,
            DateSheet.academic_term_id == academic_term_id,
        )
    ).first()

    date_sheet_subjects: list[DateSheetSubjectRead] = []
    if date_sheet and date_sheet.id:
        results = session.exec(
            select(DateSheetSubject)
            .join(
                AcademicClassSubject,
                col(AcademicClassSubject.id)
                == col(DateSheetSubject.academic_class_subject_id),
            )
            .where(DateSheetSubject.datesheet_id == date_sheet.id)
            .order_by(
                col(DateSheetSubject.exam_date).asc().nulls_last(),
                col(DateSheetSubject.start_time).asc().nulls_last(),
                col(DateSheetSubject.end_time).asc().nulls_last(),
                col(AcademicClassSubject.is_additional).asc(),
                col(AcademicClassSubject.position).asc(),
                col(DateSheetSubject.created_at).desc(),
            )
        ).all()
        date_sheet_subjects = [
            DateSheetSubjectRead.model_validate(item)
            for item in results
        ]

    return AdmitCardResponse(
        enrollment=EnrollmentRead.model_validate(enrollment),
        academic_term=AcademicTermRead.model_validate(academic_term),
        datesheet_subjects=date_sheet_subjects,
    )
