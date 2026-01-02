from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, col, select

from db import get_session
from models.subject import Subject, SubjectCreate, SubjectRead, SubjectUpdate

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
    session.commit()
    session.refresh(db_subject)
    return db_subject


@router.get("", response_model=list[SubjectRead])
def list_subjects(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = (
        select(Subject)
        .order_by(col(Subject.created_at))
        .offset(offset)
        .limit(limit)
    )
    results = session.exec(statement).all()
    return results


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
