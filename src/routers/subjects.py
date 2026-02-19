from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.subject import (Subject, SubjectCreate, SubjectListResponse,
                            SubjectRead, SubjectUpdate)

router = APIRouter(
    prefix="/subjects",
    tags=["subjects"],
)


@router.post("", response_model=SubjectRead)
def create_subject(
    subject: SubjectCreate,
    session: Session = Depends(get_session),
):
    db_subject = Subject(**subject.model_dump())
    session.add(db_subject)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Subject name already exists",
        )
    session.refresh(db_subject)
    return db_subject


@router.get("", response_model=SubjectListResponse)
def list_subjects(
    session: Session = Depends(get_session),
    search: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
):
    search_value = search.strip() if search else ""
    statement = select(Subject)
    count_statement = select(func.count()).select_from(Subject)
    if search_value:
        condition = col(Subject.name).ilike(f"%{search_value}%")
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    statement = (
        statement
        .order_by(
            col(Subject.name),
            col(Subject.created_at).desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    items = cast(list[SubjectRead], session.exec(statement).all())
    return SubjectListResponse(total=total, items=items)


@router.get("/{subject_id}", response_model=SubjectRead)
def get_subject(
    subject_id: UUID,
    session: Session = Depends(get_session),
):
    subject = session.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.patch("/{subject_id}", response_model=SubjectRead)
def partial_update_subject(
    subject_id: UUID,
    subject: SubjectUpdate,
    session: Session = Depends(get_session),
):
    db_subject = session.get(Subject, subject_id)
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    update_data = subject.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_subject, key, value)

    session.add(db_subject)
    session.commit()
    session.refresh(db_subject)
    return db_subject


@router.delete("/{subject_id}")
def delete_subject(
    subject_id: UUID,
    session: Session = Depends(get_session),
):
    db_subject = session.get(Subject, subject_id)
    if not db_subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    session.delete(db_subject)
    session.commit()
    return {"message": "Subject deleted"}
