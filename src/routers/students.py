from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from db import get_session
from models.student import (Student, StudentCreate, StudentListResponse,
                            StudentRead, StudentReadRaw, StudentUpdate)

router = APIRouter(
    prefix="/students",
    tags=["students"]
)


@router.post("", response_model=StudentRead)
def create_student(
    student: StudentCreate,
    session: Session = Depends(get_session),
):
    db_student = Student(**student.model_dump())
    session.add(db_student)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Student registration number already exists",
        )
    session.refresh(db_student)
    return db_student


@router.get("", response_model=StudentListResponse)
def list_students(
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    total = session.exec(select(func.count()).select_from(Student)).one()
    statement = select(Student).offset(offset).limit(limit)
    items = session.exec(statement).all()
    return StudentListResponse(total=total, items=items)  # type:ignore


@router.get("/raw", response_model=list[StudentReadRaw])
def list_raw_students(session: Session = Depends(get_session)):
    statement = select(Student)
    results = session.exec(statement).all()
    return results


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: UUID,
    session: Session = Depends(get_session),
):
    statement = (
        select(Student)
        .where(Student.id == student_id)

    )
    student = session.exec(statement).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.patch("/{student_id}", response_model=StudentRead)
def partial_update_student(
    student_id: UUID,
    student: StudentUpdate,
    session: Session = Depends(get_session),
):
    db_student = session.get(Student, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    update_data = student.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_student, key, value)

    session.add(db_student)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Student registration number already exists",
        )
    session.refresh(db_student)
    return db_student


@router.delete("/{student_id}")
def delete_student(
    student_id: UUID,
    session: Session = Depends(get_session),
):
    db_student = session.get(Student, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    session.delete(db_student)
    session.commit()
    return {"message": "Student deleted"}
