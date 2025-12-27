

from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from db import get_session
from models.student import (
    Student,
    StudentCreate,
    StudentRead,
    StudentUpdate,
)

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
    session.commit()
    session.refresh(db_student)
    return db_student


@router.get("", response_model=list[StudentRead])
def list_students(session: Session = Depends(get_session)):
    statement = select(Student)
    results = session.exec(statement).all()
    return results


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: int,
    session: Session = Depends(get_session),
):
    student = session.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@router.patch("/{student_id}", response_model=StudentRead)
def partial_update_student(
    student_id: int,
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
    session.commit()
    session.refresh(db_student)
    return db_student


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    session: Session = Depends(get_session),
):
    db_student = session.get(Student, student_id)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")

    session.delete(db_student)
    session.commit()
    return {"message": "Student deleted"}
