from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from db import get_session
from models.academic_class import AcademicClass
from models.academic_class_subject import AcademicClassSubject
from models.academic_term import AcademicTerm
from models.datesheet import DateSheet, DateSheetCreate, DateSheetRead
from models.datesheet_subject import DateSheetSubject

router = APIRouter(
    prefix="/date-sheets",
    tags=["date-sheets"],
)


@router.post("", response_model=DateSheetRead)
def create_date_sheet(
    date_sheet: DateSheetCreate,
    session: Session = Depends(get_session),
):
    academic_class = session.get(AcademicClass, date_sheet.academic_class_id)
    if not academic_class:
        raise HTTPException(
            status_code=404, detail="Academic class not found"
        )
    academic_term = session.get(AcademicTerm, date_sheet.academic_term_id)
    if not academic_term:
        raise HTTPException(
            status_code=404, detail="Academic term not found"
        )

    db_date_sheet = DateSheet(**date_sheet.model_dump())
    session.add(db_date_sheet)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Date sheet already exists"
        )
    if db_date_sheet.id is None:
        raise HTTPException(
            status_code=500, detail="Date sheet ID was not generated"
        )

    class_subject_ids_raw = session.exec(
        select(AcademicClassSubject.id).where(
            AcademicClassSubject.academic_class_id
            == date_sheet.academic_class_id,
            AcademicClassSubject.academic_term_id
            == date_sheet.academic_term_id,
        )
    ).all()
    class_subject_ids = [
        class_subject_id
        for class_subject_id in class_subject_ids_raw
        if class_subject_id is not None
    ]
    if class_subject_ids:
        session.add_all(
            [
                DateSheetSubject(
                    datesheet_id=db_date_sheet.id,
                    academic_class_subject_id=class_subject_id,
                )
                for class_subject_id in class_subject_ids
            ]
        )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Date sheet subjects already exist",
        )
    session.refresh(db_date_sheet)
    return db_date_sheet
