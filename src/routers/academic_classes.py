from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from db import get_session
from models.academic_class import (AcademicClass, AcademicClassCreate,
                                   AcademicClassRead, AcademicClassUpdate)

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


@router.get("", response_model=list[AcademicClassRead])
def list_academic_classes(
    academic_session_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(AcademicClass)
    if academic_session_id:
        statement = statement.where(
            AcademicClass.academic_session_id == academic_session_id
        )
    results = session.exec(statement).all()
    return results


@router.get("/{academic_class_id}", response_model=AcademicClassRead)
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
