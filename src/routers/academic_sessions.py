from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class import AcademicClass
from models.academic_session import (AcademicSession, AcademicSessionCreate,
                                     AcademicSessionListResponse,
                                     AcademicSessionRead,
                                     AcademicSessionUpdate)
from models.academic_term import AcademicTerm, AcademicTermType

router = APIRouter(
    prefix="/academic-sessions",
    tags=["academic-sessions"],
)


@router.post("", response_model=AcademicSessionRead)
def create_academic_session(
    academic_session: AcademicSessionCreate,
    session: Session = Depends(get_session),
):
    db_academic_session = AcademicSession(**academic_session.model_dump())
    session.add(db_academic_session)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Academic session already exists for this year",
        )
    session.refresh(db_academic_session)
    return db_academic_session


@router.get("", response_model=AcademicSessionListResponse)
def list_academic_sessions(
    year: str | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = select(AcademicSession)
    count_statement = select(func.count()).select_from(AcademicSession)
    if year:
        condition = AcademicSession.year == year
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(
            col(AcademicSession.year),
            col(AcademicSession.created_at).desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[AcademicSessionRead], results)
    return AcademicSessionListResponse(total=total, items=items)


@router.get("/{academic_session_id}", response_model=AcademicSessionRead)
def get_academic_session(
    academic_session_id: UUID,
    session: Session = Depends(get_session),
):
    academic_session = session.get(AcademicSession, academic_session_id)
    if not academic_session:
        raise HTTPException(
            status_code=404, detail="Academic session not found")
    return academic_session


@router.patch("/{academic_session_id}", response_model=AcademicSessionRead)
def partial_update_academic_session(
    academic_session_id: UUID,
    academic_session: AcademicSessionUpdate,
    session: Session = Depends(get_session),
):
    db_academic_session = session.get(AcademicSession, academic_session_id)
    if not db_academic_session:
        raise HTTPException(
            status_code=404, detail="Academic session not found")

    update_data = academic_session.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_academic_session, key, value)

    session.add(db_academic_session)
    session.commit()
    session.refresh(db_academic_session)
    return db_academic_session


@router.delete("/{academic_session_id}")
def delete_academic_session(
    academic_session_id: UUID,
    session: Session = Depends(get_session),
):
    db_academic_session = session.get(AcademicSession, academic_session_id)
    if not db_academic_session:
        raise HTTPException(
            status_code=404, detail="Academic session not found")

    session.delete(db_academic_session)
    session.commit()
    return {"message": "Academic session deleted"}


@router.post("/{academic_session_id}/create-academic-terms")
def create_academic_terms(
    academic_session_id: UUID,
    session: Session = Depends(get_session),
):
    db_academic_session = session.get(AcademicSession, academic_session_id)
    if not db_academic_session:
        raise HTTPException(
            status_code=404, detail="Academic session not found")

    desired_terms = [
        AcademicTermType.QUARTERLY,
        AcademicTermType.HALF_YEARLY,
        AcademicTermType.ANNUAL,
    ]
    existing_terms = session.exec(
        select(AcademicTerm).where(
            AcademicTerm.academic_session_id == academic_session_id
        )
    ).all()
    existing_types = {term.term_type for term in existing_terms}
    new_terms = [
        AcademicTerm(
            academic_session_id=academic_session_id,
            term_type=term_type,
        )
        for term_type in desired_terms
        if term_type not in existing_types
    ]
    if new_terms:
        session.add_all(new_terms)
        session.commit()

    existing = [term_type for term_type in desired_terms
                if term_type in existing_types]
    created = [term.term_type for term in new_terms]
    return {
        "created": created,
        "existing": existing,
        "total": len(existing) + len(created),
    }


class_grades = [
    "PRE-NURSERY",
    "NURSERY",
    "LKG",
    "UKG",
    "I",
    "II",
    "III",
    "IV",
    "V",
    "VI",
    "VII",
    "VIII",
]


@router.post("/{academic_session_id}/create-academic-classes")
def create_academic_classes(
    academic_session_id: UUID,
    session: Session = Depends(get_session),
):
    db_academic_session = session.get(AcademicSession, academic_session_id)
    if not db_academic_session:
        raise HTTPException(
            status_code=404, detail="Academic session not found")

    existing_classes = session.exec(
        select(AcademicClass).where(
            AcademicClass.academic_session_id == academic_session_id,
            AcademicClass.section == "A",
        )
    ).all()
    existing_grades = {academic_class.grade
                       for academic_class in existing_classes}
    new_classes = [
        AcademicClass(
            academic_session_id=academic_session_id,
            grade=grade,
            section="A",
        )
        for grade in class_grades
        if grade not in existing_grades
    ]
    if new_classes:
        session.add_all(new_classes)
        session.commit()

    existing = [grade for grade in class_grades if grade in existing_grades]
    created = [academic_class.grade for academic_class in new_classes]
    return {
        "created": created,
        "existing": existing,
        "total": len(existing) + len(created),
    }
