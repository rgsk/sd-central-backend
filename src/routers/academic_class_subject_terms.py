from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class_subject_term import (
    AcademicClassSubjectTerm, AcademicClassSubjectTermCreate,
    AcademicClassSubjectTermListResponse, AcademicClassSubjectTermRead,
    AcademicClassSubjectTermUpdate)

router = APIRouter(
    prefix="/academic-class-subject-terms",
    tags=["academic-class-subject-terms"],
)


@router.post("", response_model=AcademicClassSubjectTermRead)
def create_academic_class_subject_term(
    academic_class_subject_term: AcademicClassSubjectTermCreate,
    session: Session = Depends(get_session),
):
    db_term = AcademicClassSubjectTerm(
        **academic_class_subject_term.model_dump()
    )
    session.add(db_term)
    try:
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Academic class subject term already exists",
        )
    session.refresh(db_term)
    return db_term


@router.get("", response_model=AcademicClassSubjectTermListResponse)
def list_academic_class_subject_terms(
    academic_class_subject_id: UUID | None = Query(default=None),
    academic_term_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
):
    statement = select(AcademicClassSubjectTerm)
    count_statement = select(func.count()).select_from(
        AcademicClassSubjectTerm
    )
    if academic_class_subject_id:
        condition = (
            AcademicClassSubjectTerm.academic_class_subject_id
            == academic_class_subject_id
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_term_id:
        condition = (
            AcademicClassSubjectTerm.academic_term_id == academic_term_id
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(

            col(AcademicClassSubjectTerm.created_at).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[AcademicClassSubjectTermRead], results)
    return AcademicClassSubjectTermListResponse(total=total, items=items)


@router.get("/find", response_model=AcademicClassSubjectTermRead)
def find_academic_class_subject_term(
    academic_class_subject_id: UUID = Query(...),
    academic_term_id: UUID = Query(...),
    session: Session = Depends(get_session),
):
    db_term = session.exec(
        select(AcademicClassSubjectTerm).where(
            AcademicClassSubjectTerm.academic_class_subject_id
            == academic_class_subject_id,
            AcademicClassSubjectTerm.academic_term_id == academic_term_id,
        )
    ).first()
    if not db_term:
        raise HTTPException(
            status_code=404,
            detail="Academic class subject term not found",
        )
    return db_term


@router.get(
    "/{academic_class_subject_term_id}",
    response_model=AcademicClassSubjectTermRead,
)
def get_academic_class_subject_term(
    academic_class_subject_term_id: UUID,
    session: Session = Depends(get_session),
):
    db_term = session.get(
        AcademicClassSubjectTerm, academic_class_subject_term_id
    )
    if not db_term:
        raise HTTPException(
            status_code=404,
            detail="Academic class subject term not found",
        )
    return db_term


@router.patch(
    "/{academic_class_subject_term_id}",
    response_model=AcademicClassSubjectTermRead,
)
def partial_update_academic_class_subject_term(
    academic_class_subject_term_id: UUID,
    academic_class_subject_term: AcademicClassSubjectTermUpdate,
    session: Session = Depends(get_session),
):
    db_term = session.get(
        AcademicClassSubjectTerm, academic_class_subject_term_id
    )
    if not db_term:
        raise HTTPException(
            status_code=404,
            detail="Academic class subject term not found",
        )
    update_data = academic_class_subject_term.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_term, key, value)
    session.add(db_term)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Academic class subject term already exists",
        )
    session.refresh(db_term)
    return db_term


@router.delete("/{academic_class_subject_term_id}")
def delete_academic_class_subject_term(
    academic_class_subject_term_id: UUID,
    session: Session = Depends(get_session),
):
    db_term = session.get(
        AcademicClassSubjectTerm, academic_class_subject_term_id
    )
    if not db_term:
        raise HTTPException(
            status_code=404,
            detail="Academic class subject term not found",
        )
    session.delete(db_term)
    session.commit()
    return {"message": "Academic class subject term deleted"}
