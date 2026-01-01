from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from db import get_session
from models.academic_session import (
    AcademicSession,
    AcademicSessionCreate,
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


@router.get("", response_model=list[AcademicSessionRead])
def list_academic_sessions(
    year: str | None = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(AcademicSession)
    if year:
        statement = statement.where(AcademicSession.year == year)
    results = session.exec(statement).all()
    return results


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
