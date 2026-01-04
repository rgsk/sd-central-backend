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
                                           AcademicClassSubjectReadWithSubject,
                                           AcademicClassSubjectUpdate)

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
        statement.order_by(col(AcademicClassSubject.created_at).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[AcademicClassSubjectReadWithSubject], results)
    return AcademicClassSubjectListResponse(total=total, items=items)


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
