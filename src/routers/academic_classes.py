from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class import (
    AcademicClass,
    AcademicClassCreate,
    AcademicClassListResponse,
    AcademicClassRead,
    AcademicClassReadWithSubjects,
    AcademicClassUpdate,
)

router = APIRouter(
    prefix="/academic-classes",
    tags=["academic-classes"]
)


@router.post("", response_model=AcademicClassRead)
def create_academic_class(
    academic_class: AcademicClassCreate,
    session: Session = Depends(get_session),
):
    db_academic_class = AcademicClass(**academic_class.model_dump())
    session.add(db_academic_class)
    session.commit()
    session.refresh(db_academic_class)
    return db_academic_class


@router.get("", response_model=AcademicClassListResponse)
def list_academic_classes(
    academic_session_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = select(AcademicClass)
    count_statement = select(func.count()).select_from(AcademicClass)
    if academic_session_id:
        condition = AcademicClass.academic_session_id == academic_session_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(col(AcademicClass.created_at).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[AcademicClassRead], results)
    return AcademicClassListResponse(total=total, items=items)


@router.get(
    "/{academic_class_id}",
    response_model=AcademicClassReadWithSubjects,
)
def get_academic_class(
    academic_class_id: UUID,
    session: Session = Depends(get_session),
):
    academic_class = session.get(AcademicClass, academic_class_id)
    if not academic_class:
        raise HTTPException(status_code=404, detail="Academic class not found")
    return academic_class


@router.patch("/{academic_class_id}", response_model=AcademicClassRead)
def partial_update_academic_class(
    academic_class_id: UUID,
    academic_class: AcademicClassUpdate,
    session: Session = Depends(get_session),
):
    db_academic_class = session.get(AcademicClass, academic_class_id)
    if not db_academic_class:
        raise HTTPException(status_code=404, detail="Academic class not found")

    update_data = academic_class.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_academic_class, key, value)

    session.add(db_academic_class)
    session.commit()
    session.refresh(db_academic_class)
    return db_academic_class


@router.delete("/{academic_class_id}")
def delete_academic_class(
    academic_class_id: UUID,
    session: Session = Depends(get_session),
):
    db_academic_class = session.get(AcademicClass, academic_class_id)
    if not db_academic_class:
        raise HTTPException(status_code=404, detail="Academic class not found")

    session.delete(db_academic_class)
    session.commit()
    return {"message": "Academic class deleted"}
