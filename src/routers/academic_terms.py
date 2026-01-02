from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, col, select

from db import get_session
from models.academic_term import (AcademicTerm, AcademicTermCreate,
                                  AcademicTermRead, AcademicTermUpdate)

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
    session.commit()
    session.refresh(db_academic_term)
    return db_academic_term


@router.get("", response_model=list[AcademicTermRead])
def list_academic_terms(
    academic_session_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = select(AcademicTerm)
    if academic_session_id:
        statement = statement.where(
            AcademicTerm.academic_session_id == academic_session_id
        )
    results = session.exec(
        statement.order_by(col(AcademicTerm.created_at))
        .offset(offset)
        .limit(limit)
    ).all()
    return results


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
