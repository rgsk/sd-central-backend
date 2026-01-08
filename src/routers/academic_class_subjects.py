from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class_subject import (AcademicClassSubject,
                                           AcademicClassSubjectCreate,
                                           AcademicClassSubjectListResponse,
                                           AcademicClassSubjectReorderRequest,
                                           AcademicClassSubjectReadWithSubject,
                                           AcademicClassSubjectUpdate)
from models.datesheet import DateSheet
from models.datesheet_subject import DateSheetSubject
from models.enrollment import Enrollment
from models.report_card import ReportCard
from models.report_card_subject import ReportCardSubject

router = APIRouter(
    prefix="/academic-class-subjects",
    tags=["academic-class-subjects"],
)


@router.post("", response_model=AcademicClassSubjectReadWithSubject)
def create_academic_class_subject(
    academic_class_subject: AcademicClassSubjectCreate,
    session: Session = Depends(get_session),
):
    db_class_subject = AcademicClassSubject(
        **academic_class_subject.model_dump()
    )
    session.add(db_class_subject)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Subject already exists for this class",
        )
    session.refresh(db_class_subject)
    if db_class_subject.id is None:
        raise HTTPException(
            status_code=500,
            detail="Academic class subject ID was not generated",
        )
    report_card_ids_raw = session.exec(
        select(ReportCard.id)
        .join(
            Enrollment,
            col(Enrollment.id) == col(ReportCard.enrollment_id),
        )
        .where(
            Enrollment.academic_class_id
            == academic_class_subject.academic_class_id,
            ReportCard.academic_term_id
            == academic_class_subject.academic_term_id,
        )
    ).all()
    report_card_ids = [
        report_card_id
        for report_card_id in report_card_ids_raw
        if report_card_id is not None
    ]
    if report_card_ids:
        existing_report_card_ids_raw = session.exec(
            select(ReportCardSubject.report_card_id).where(
                ReportCardSubject.academic_class_subject_id
                == db_class_subject.id,
                col(ReportCardSubject.report_card_id).in_(report_card_ids),
            )
        ).all()
        existing_report_card_ids = [
            report_card_id
            for report_card_id in existing_report_card_ids_raw
            if report_card_id is not None
        ]
        missing_report_card_ids = set(report_card_ids) - set(
            existing_report_card_ids
        )
        if missing_report_card_ids:
            new_subjects = [
                ReportCardSubject(
                    report_card_id=report_card_id,
                    academic_class_subject_id=db_class_subject.id,
                )
                for report_card_id in missing_report_card_ids
            ]
            session.add_all(new_subjects)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
    date_sheet_ids_raw = session.exec(
        select(DateSheet.id).where(
            DateSheet.academic_class_id
            == academic_class_subject.academic_class_id,
            DateSheet.academic_term_id
            == academic_class_subject.academic_term_id,
        )
    ).all()
    date_sheet_ids = [
        date_sheet_id
        for date_sheet_id in date_sheet_ids_raw
        if date_sheet_id is not None
    ]
    if date_sheet_ids:
        existing_date_sheet_ids_raw = session.exec(
            select(DateSheetSubject.datesheet_id).where(
                DateSheetSubject.academic_class_subject_id
                == db_class_subject.id,
                col(DateSheetSubject.datesheet_id).in_(date_sheet_ids),
            )
        ).all()
        existing_date_sheet_ids = [
            date_sheet_id
            for date_sheet_id in existing_date_sheet_ids_raw
            if date_sheet_id is not None
        ]
        missing_date_sheet_ids = set(date_sheet_ids) - set(
            existing_date_sheet_ids
        )
        if missing_date_sheet_ids:
            new_date_sheet_subjects = [
                DateSheetSubject(
                    datesheet_id=date_sheet_id,
                    academic_class_subject_id=db_class_subject.id,
                )
                for date_sheet_id in missing_date_sheet_ids
            ]
            session.add_all(new_date_sheet_subjects)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
    return db_class_subject


@router.get("", response_model=AcademicClassSubjectListResponse)
def list_academic_class_subjects(
    academic_class_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
    academic_term_id: UUID | None = Query(default=None),
    is_additional: bool | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = select(AcademicClassSubject)
    count_statement = select(func.count()).select_from(AcademicClassSubject)
    if academic_class_id:
        condition = AcademicClassSubject.academic_class_id == academic_class_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if subject_id:
        condition = AcademicClassSubject.subject_id == subject_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_term_id:
        condition = AcademicClassSubject.academic_term_id == academic_term_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if is_additional is not None:
        condition = AcademicClassSubject.is_additional == is_additional
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(
            col(AcademicClassSubject.position).asc(),
            col(AcademicClassSubject.created_at).desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[AcademicClassSubjectReadWithSubject], results)
    return AcademicClassSubjectListResponse(total=total, items=items)


@router.patch("/reorder", response_model=AcademicClassSubjectListResponse)
def reorder_academic_class_subjects(
    payload: AcademicClassSubjectReorderRequest,
    session: Session = Depends(get_session),
):
    if not payload.items:
        raise HTTPException(
            status_code=400, detail="Reorder list cannot be empty"
        )

    ids = [item.id for item in payload.items]
    items_by_id = {item.id: item.position for item in payload.items}
    if len(set(items_by_id.values())) != len(items_by_id):
        raise HTTPException(
            status_code=400,
            detail="Positions must be unique within the reorder list",
        )
    statement = select(AcademicClassSubject).where(
        col(AcademicClassSubject.id).in_(ids)
    )
    db_items = session.exec(statement).all()

    if len(db_items) != len(ids):
        found_ids = {item.id for item in db_items if item.id is not None}
        missing_ids = [str(item_id) for item_id in ids if item_id not in found_ids]
        raise HTTPException(
            status_code=404,
            detail=f"Academic class subjects not found: {', '.join(missing_ids)}",
        )

    group_keys = {
        (
            item.academic_class_id,
            item.academic_term_id,
            item.is_additional,
        )
        for item in db_items
    }
    if len(group_keys) != 1:
        raise HTTPException(
            status_code=400,
            detail="Reorder list must belong to the same class, term, and group",
        )
    academic_class_id, academic_term_id, is_additional = next(iter(group_keys))
    max_position = session.exec(
        select(func.max(AcademicClassSubject.position)).where(
            AcademicClassSubject.academic_class_id == academic_class_id,
            AcademicClassSubject.academic_term_id == academic_term_id,
            AcademicClassSubject.is_additional == is_additional,
        )
    ).one()
    base_position = (max_position or 0) + 1000
    for idx, db_item in enumerate(db_items):
        if db_item.id is not None:
            db_item.position = base_position + idx + 1
            session.add(db_item)
    session.commit()

    for db_item in db_items:
        if db_item.id is not None:
            db_item.position = items_by_id[db_item.id]
            session.add(db_item)
    session.commit()
    results = session.exec(
        select(AcademicClassSubject).where(
            col(AcademicClassSubject.id).in_(ids)
        ).order_by(
            col(AcademicClassSubject.position).asc(),
            col(AcademicClassSubject.created_at).desc(),
        )
    ).all()
    items = cast(list[AcademicClassSubjectReadWithSubject], results)
    return AcademicClassSubjectListResponse(total=len(items), items=items)


@router.get(
    "/{academic_class_subject_id}",
    response_model=AcademicClassSubjectReadWithSubject,
)
def get_academic_class_subject(
    academic_class_subject_id: UUID,
    session: Session = Depends(get_session),
):
    statement = (
        select(AcademicClassSubject)
        .where(AcademicClassSubject.id == academic_class_subject_id)
    )
    class_subject = session.exec(statement).one_or_none()
    if not class_subject:
        raise HTTPException(
            status_code=404,
            detail="Academic class subject not found",
        )
    return class_subject


@router.patch(
    "/{academic_class_subject_id}",
    response_model=AcademicClassSubjectReadWithSubject,
)
def partial_update_academic_class_subject(
    academic_class_subject_id: UUID,
    academic_class_subject: AcademicClassSubjectUpdate,
    session: Session = Depends(get_session),
):
    db_class_subject = session.get(
        AcademicClassSubject, academic_class_subject_id
    )
    if not db_class_subject:
        raise HTTPException(
            status_code=404,
            detail="Academic class subject not found",
        )

    update_data = academic_class_subject.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_class_subject, key, value)

    session.add(db_class_subject)
    session.commit()
    session.refresh(db_class_subject)
    return db_class_subject


@router.delete("/{academic_class_subject_id}")
def delete_academic_class_subject(
    academic_class_subject_id: UUID,
    session: Session = Depends(get_session),
):
    db_class_subject = session.get(
        AcademicClassSubject, academic_class_subject_id
    )
    if not db_class_subject:
        raise HTTPException(
            status_code=404,
            detail="Academic class subject not found",
        )
    session.delete(db_class_subject)
    session.commit()
    return {"message": "Academic class subject deleted"}
