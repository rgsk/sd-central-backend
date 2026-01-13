from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class import AcademicClass
from models.academic_class_subject import AcademicClassSubject
from models.academic_term import AcademicTerm
from models.date_sheet import (DateSheet, DateSheetCreate,
                               DateSheetListResponse, DateSheetRead,
                               DateSheetUpdate)
from models.date_sheet_subject import DateSheetSubject

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
                    date_sheet_id=db_date_sheet.id,
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


@router.get("", response_model=DateSheetListResponse)
def list_date_sheets(
    academic_class_id: UUID | None = Query(default=None),
    academic_term_id: UUID | None = Query(default=None),
    academic_session_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = select(DateSheet).join(
        AcademicClass,
        col(AcademicClass.id) == col(DateSheet.academic_class_id),
    )
    count_statement = select(func.count()).select_from(DateSheet)
    if academic_session_id:
        statement = statement.join(
            AcademicTerm,
            col(AcademicTerm.id) == col(DateSheet.academic_term_id),
        )
        count_statement = count_statement.join(
            AcademicTerm,
            col(AcademicTerm.id) == col(DateSheet.academic_term_id),
        )
    if academic_class_id:
        condition = DateSheet.academic_class_id == academic_class_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_term_id:
        condition = DateSheet.academic_term_id == academic_term_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_session_id:
        condition = AcademicTerm.academic_session_id == academic_session_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(
            col(AcademicClass.grade).asc(),
            col(AcademicClass.section).asc(),
            col(DateSheet.created_at).desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[DateSheetRead], results)
    return DateSheetListResponse(total=total, items=items)


@router.get("/{date_sheet_id}", response_model=DateSheetRead)
def get_date_sheet(
    date_sheet_id: UUID,
    session: Session = Depends(get_session),
):
    date_sheet = session.get(DateSheet, date_sheet_id)
    if not date_sheet:
        raise HTTPException(status_code=404, detail="Date sheet not found")
    return date_sheet


@router.patch("/{date_sheet_id}", response_model=DateSheetRead)
def partial_update_date_sheet(
    date_sheet_id: UUID,
    date_sheet: DateSheetUpdate,
    session: Session = Depends(get_session),
):
    db_date_sheet = session.get(DateSheet, date_sheet_id)
    if not db_date_sheet:
        raise HTTPException(status_code=404, detail="Date sheet not found")

    update_data = date_sheet.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_date_sheet, key, value)

    session.add(db_date_sheet)
    session.commit()
    session.refresh(db_date_sheet)
    return db_date_sheet


@router.delete("/{date_sheet_id}")
def delete_date_sheet(
    date_sheet_id: UUID,
    session: Session = Depends(get_session),
):
    db_date_sheet = session.get(DateSheet, date_sheet_id)
    if not db_date_sheet:
        raise HTTPException(status_code=404, detail="Date sheet not found")

    session.delete(db_date_sheet)
    session.commit()
    return {"message": "Date sheet deleted"}
