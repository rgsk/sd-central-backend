from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class import AcademicClass
from models.academic_session import AcademicSession
from models.class_student import (ClassStudent, ClassStudentCreate,
                                  ClassStudentListResponse, ClassStudentRead,
                                  ClassStudentUpdate)
from models.student import Student

router = APIRouter(
    prefix="/class-students",
    tags=["class-students"],
)


@router.post("", response_model=ClassStudentRead)
def create_class_student(
    class_student: ClassStudentCreate,
    session: Session = Depends(get_session),
):
    student = session.get(Student, class_student.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    academic_class = session.get(
        AcademicClass, class_student.academic_class_id
    )
    if not academic_class:
        raise HTTPException(
            status_code=404, detail="Academic class not found"
        )
    if academic_class.academic_session_id != class_student.academic_session_id:
        raise HTTPException(
            status_code=400,
            detail="Academic session does not match the class session",
        )

    db_class_student = ClassStudent(**class_student.model_dump())
    session.add(db_class_student)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Class student already exists",
        )
    session.refresh(db_class_student)
    return db_class_student


@router.get("", response_model=ClassStudentListResponse)
def list_class_students(
    student_id: UUID | None = Query(default=None),
    academic_class_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = (
        select(ClassStudent)
        .join(
            AcademicSession,
            col(AcademicSession.id)
            == col(ClassStudent.academic_session_id),
        )
    )
    count_statement = select(func.count()).select_from(ClassStudent)
    if student_id:
        condition = ClassStudent.student_id == student_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_class_id:
        condition = ClassStudent.academic_class_id == academic_class_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(
            col(AcademicSession.year),
            col(ClassStudent.created_at).desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[ClassStudentRead], results)
    return ClassStudentListResponse(total=total, items=items)


@router.get("/{class_student_id}", response_model=ClassStudentRead)
def get_class_student(
    class_student_id: UUID,
    session: Session = Depends(get_session),
):
    class_student = session.get(ClassStudent, class_student_id)
    if not class_student:
        raise HTTPException(
            status_code=404, detail="Class student not found"
        )
    return class_student


@router.patch("/{class_student_id}", response_model=ClassStudentRead)
def partial_update_class_student(
    class_student_id: UUID,
    class_student: ClassStudentUpdate,
    session: Session = Depends(get_session),
):
    db_class_student = session.get(ClassStudent, class_student_id)
    if not db_class_student:
        raise HTTPException(
            status_code=404, detail="Class student not found"
        )

    update_data = class_student.model_dump(exclude_unset=True)
    if "student_id" in update_data:
        student = session.get(Student, update_data["student_id"])
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
    academic_class = None
    if "academic_class_id" in update_data:
        academic_class = session.get(
            AcademicClass, update_data["academic_class_id"]
        )
        if not academic_class:
            raise HTTPException(
                status_code=404, detail="Academic class not found"
            )
    if "academic_session_id" in update_data or academic_class is not None:
        next_session_id = update_data.get(
            "academic_session_id", db_class_student.academic_session_id
        )
        next_class = academic_class or session.get(
            AcademicClass, db_class_student.academic_class_id
        )
        if next_class and next_class.academic_session_id != next_session_id:
            raise HTTPException(
                status_code=400,
                detail="Academic session does not match the class session",
            )

    for key, value in update_data.items():
        setattr(db_class_student, key, value)

    session.add(db_class_student)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Class student already exists",
        )
    session.refresh(db_class_student)
    return db_class_student


@router.delete("/{class_student_id}")
def delete_class_student(
    class_student_id: UUID,
    session: Session = Depends(get_session),
):
    db_class_student = session.get(ClassStudent, class_student_id)
    if not db_class_student:
        raise HTTPException(
            status_code=404, detail="Class student not found"
        )
    session.delete(db_class_student)
    session.commit()
    return {"message": "Class student deleted"}
