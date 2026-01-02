from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, col, select

from db import get_session
from models.academic_session import (
    AcademicSession,
    AcademicSessionCreate,
    AcademicSessionListResponse,
    AcademicSessionRead,
    AcademicSessionUpdate,
)

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
    session.commit()
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
        statement.order_by(col(AcademicSession.created_at))
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
        raise HTTPException(status_code=404, detail="Academic session not found")
    return academic_session


@router.patch("/{academic_session_id}", response_model=AcademicSessionRead)
def partial_update_academic_session(
    academic_session_id: UUID,
    academic_session: AcademicSessionUpdate,
    session: Session = Depends(get_session),
):
    db_academic_session = session.get(AcademicSession, academic_session_id)
    if not db_academic_session:
        raise HTTPException(status_code=404, detail="Academic session not found")

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
        raise HTTPException(status_code=404, detail="Academic session not found")

    session.delete(db_academic_session)
    session.commit()
    return {"message": "Academic session deleted"}
