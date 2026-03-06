from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class_subject import AcademicClassSubject
from models.date_sheet_subject import (DateSheetSubject,
                                       DateSheetSubjectBulkUpdate,
                                       DateSheetSubjectBulkUpdateResponse,
                                       DateSheetSubjectCreate,
                                       DateSheetSubjectListResponse,
                                       DateSheetSubjectRead,
                                       DateSheetSubjectUpdate)

router = APIRouter(
    prefix="/date-sheet-subjects",
    tags=["date-sheet-subjects"],
)


@router.post("", response_model=DateSheetSubjectRead)
def create_date_sheet_subject(
    date_sheet_subject: DateSheetSubjectCreate,
    session: Session = Depends(get_session),
):
    db_date_sheet_subject = DateSheetSubject(
        **date_sheet_subject.model_dump()
    )
    session.add(db_date_sheet_subject)
    session.commit()
    session.refresh(db_date_sheet_subject)
    return db_date_sheet_subject


@router.get("", response_model=DateSheetSubjectListResponse)
def list_date_sheet_subjects(
    date_sheet_id: UUID | None = Query(default=None),
    academic_class_subject_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
):
    statement = select(DateSheetSubject)
    count_statement = select(func.count()).select_from(DateSheetSubject)
    if date_sheet_id:
        condition = DateSheetSubject.date_sheet_id == date_sheet_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_class_subject_id:
        condition = (
            DateSheetSubject.academic_class_subject_id
            == academic_class_subject_id
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.join(
            AcademicClassSubject,
            col(AcademicClassSubject.id)
            == col(DateSheetSubject.academic_class_subject_id),
        )
        .order_by(
            col(DateSheetSubject.exam_date).asc().nulls_last(),
            col(DateSheetSubject.start_time).asc().nulls_last(),
            col(DateSheetSubject.end_time).asc().nulls_last(),
            col(AcademicClassSubject.is_additional).asc(),
            col(AcademicClassSubject.position).asc(),
            col(DateSheetSubject.created_at).desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[DateSheetSubjectRead], results)
    return DateSheetSubjectListResponse(total=total, items=items)


@router.patch("/bulk", response_model=DateSheetSubjectBulkUpdateResponse)
def bulk_update_date_sheet_subjects(
    payload: DateSheetSubjectBulkUpdate,
    session: Session = Depends(get_session),
):
    if not payload.items:
        return DateSheetSubjectBulkUpdateResponse(items=[])

    ids = [item.id for item in payload.items]
    results = session.exec(
        select(DateSheetSubject).where(
            col(DateSheetSubject.id).in_(ids)
        )
    ).all()
    if len(results) != len(ids):
        found_ids = {subject.id for subject in results}
        missing_ids = [
            str(subject_id)
            for subject_id in ids
            if subject_id not in found_ids
        ]
        raise HTTPException(
            status_code=404,
            detail=(
                "Date sheet subjects not found: "
                + ", ".join(missing_ids)
            ),
        )

    subject_map = {subject.id: subject for subject in results}
    for item in payload.items:
        db_date_sheet_subject = subject_map[item.id]
        update_data = item.model_dump(exclude={"id"}, exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_date_sheet_subject, key, value)
        session.add(db_date_sheet_subject)

    session.commit()
    for subject in subject_map.values():
        session.refresh(subject)

    updated_subjects = [
        subject_map[item.id] for item in payload.items
    ]
    return DateSheetSubjectBulkUpdateResponse(
        items=cast(list[DateSheetSubjectRead], updated_subjects)
    )


@router.get("/{date_sheet_subject_id}", response_model=DateSheetSubjectRead)
def get_date_sheet_subject(
    date_sheet_subject_id: UUID,
    session: Session = Depends(get_session),
):
    date_sheet_subject = session.get(
        DateSheetSubject, date_sheet_subject_id
    )
    if not date_sheet_subject:
        raise HTTPException(
            status_code=404, detail="Date sheet subject not found"
        )
    return date_sheet_subject


@router.patch("/{date_sheet_subject_id}", response_model=DateSheetSubjectRead)
def partial_update_date_sheet_subject(
    date_sheet_subject_id: UUID,
    date_sheet_subject: DateSheetSubjectUpdate,
    session: Session = Depends(get_session),
):
    db_date_sheet_subject = session.get(
        DateSheetSubject, date_sheet_subject_id
    )
    if not db_date_sheet_subject:
        raise HTTPException(
            status_code=404, detail="Date sheet subject not found"
        )

    update_data = date_sheet_subject.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_date_sheet_subject, key, value)

    session.add(db_date_sheet_subject)
    session.commit()
    session.refresh(db_date_sheet_subject)
    return db_date_sheet_subject


@router.delete("/{date_sheet_subject_id}")
def delete_date_sheet_subject(
    date_sheet_subject_id: UUID,
    session: Session = Depends(get_session),
):
    db_date_sheet_subject = session.get(
        DateSheetSubject, date_sheet_subject_id
    )
    if not db_date_sheet_subject:
        raise HTTPException(
            status_code=404, detail="Date sheet subject not found"
        )
    session.delete(db_date_sheet_subject)
    session.commit()
    return {"message": "Date sheet subject deleted"}
