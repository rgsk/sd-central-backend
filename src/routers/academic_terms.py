from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.academic_session import AcademicSession
from models.academic_term import (AcademicTerm, AcademicTermCreate,
                                  AcademicTermListResponse, AcademicTermRead,
                                  AcademicTermType, AcademicTermUpdate)

router = APIRouter(
    prefix="/academic-terms",
    tags=["academic-terms"],
)


@router.post("", response_model=AcademicTermRead)
def create_academic_term(
    academic_term: AcademicTermCreate,
    session: Session = Depends(get_session),
):
    db_academic_term = AcademicTerm(**academic_term.model_dump())
    session.add(db_academic_term)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Term already exists for this session",
        )
    session.refresh(db_academic_term)
    return db_academic_term


term_rank = case(
    (
        col(AcademicTerm.term_type) == AcademicTermType.QUARTERLY,
        0,
    ),
    (
        col(AcademicTerm.term_type) == AcademicTermType.HALF_YEARLY,
        1,
    ),
    (
        col(AcademicTerm.term_type) == AcademicTermType.ANNUAL,
        2,
    ),
    else_=3,
)


@router.get("", response_model=AcademicTermListResponse)
def list_academic_terms(
    academic_session_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
):
    statement = select(AcademicTerm).join(
        AcademicSession,
        col(AcademicSession.id) == col(AcademicTerm.academic_session_id),
    )
    count_statement = select(func.count()).select_from(AcademicTerm)
    if academic_session_id:
        condition = AcademicTerm.academic_session_id == academic_session_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(
            col(AcademicSession.year),
            term_rank,
            col(AcademicTerm.created_at).desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[AcademicTermRead], results)
    return AcademicTermListResponse(total=total, items=items)


@router.get("/{academic_term_id}", response_model=AcademicTermRead)
def get_academic_term(
    academic_term_id: UUID,
    session: Session = Depends(get_session),
):
    statement = (
        select(AcademicTerm)
        .where(AcademicTerm.id == academic_term_id)
    )
    academic_term = session.exec(statement).first()
    if not academic_term:
        raise HTTPException(status_code=404, detail="Academic term not found")
    return academic_term


@router.patch("/{academic_term_id}", response_model=AcademicTermRead)
def partial_update_academic_term(
    academic_term_id: UUID,
    academic_term: AcademicTermUpdate,
    session: Session = Depends(get_session),
):
    db_academic_term = session.get(AcademicTerm, academic_term_id)
    if not db_academic_term:
        raise HTTPException(status_code=404, detail="Academic term not found")

    update_data = academic_term.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_academic_term, key, value)

    session.add(db_academic_term)
    session.commit()
    session.refresh(db_academic_term)
    return db_academic_term


@router.delete("/{academic_term_id}")
def delete_academic_term(
    academic_term_id: UUID,
    session: Session = Depends(get_session),
):
    db_academic_term = session.get(AcademicTerm, academic_term_id)
    if not db_academic_term:
        raise HTTPException(status_code=404, detail="Academic term not found")

    session.delete(db_academic_term)
    session.commit()
    return {"message": "Academic term deleted"}
