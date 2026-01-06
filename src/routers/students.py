from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.enrollment import Enrollment, EnrollmentRead
from models.student import (Student, StudentCreate, StudentListResponse,
                            StudentRead, StudentUpdate)

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
    academic_session_id: UUID | None = Query(default=None),
    academic_class_id: UUID | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    enrollment_conditions = []
    if academic_session_id:
        enrollment_conditions.append(
            col(Enrollment.academic_session_id) == academic_session_id
        )
    if academic_class_id:
        enrollment_conditions.append(
            col(Enrollment.academic_class_id) == academic_class_id
        )

    if enrollment_conditions:
        total = session.exec(
            select(func.count(func.distinct(Student.id)))
            .select_from(Student)
            .join(
                Enrollment, col(Enrollment.student_id) == col(Student.id)
            )
            .where(*enrollment_conditions)
        ).one()
        order_by_clauses = [col(Student.created_at).desc()]
        if academic_class_id:
            order_by_clauses = [
                col(Student.name),
                col(Student.created_at).desc(),
            ]
        statement = (
            select(Student)
            .join(Enrollment, col(Enrollment.student_id) == col(Student.id))
            .where(*enrollment_conditions)
            .order_by(*order_by_clauses)
            .offset(offset)
            .limit(limit)
        )
    else:
        total = session.exec(
            select(func.count()).select_from(Student)
        ).one()
        statement = (
            select(Student)
            .order_by(col(Student.created_at).desc())
            .offset(offset)
            .limit(limit)
        )
    students = session.exec(statement).all()
    items = [StudentRead.model_validate(student) for student in students]
    if enrollment_conditions and items:
        student_ids = [
            student.id for student in items if student.id is not None
        ]
        enrollments = session.exec(
            select(Enrollment)
            .where(
                col(Enrollment.student_id).in_(student_ids),
                *enrollment_conditions,
            )
            .order_by(col(Enrollment.created_at).desc())
        ).all()
        enrollment_by_student_id: dict[UUID, EnrollmentRead] = {}
        for enrollment in enrollments:
            if enrollment.student_id not in enrollment_by_student_id:
                enrollment_by_student_id[
                    enrollment.student_id
                ] = EnrollmentRead.model_validate(enrollment)
        for student in items:
            if student.id is None:
                continue
            student.enrollment = enrollment_by_student_id.get(
                student.id
            )
    return StudentListResponse(total=total, items=items)


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: UUID,
    session: Session = Depends(get_session),
    academic_session_id: UUID | None = Query(default=None),
):
    statement = (
        select(Student)
        .where(Student.id == student_id)
    )
    student = session.exec(statement).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    read_student = StudentRead.model_validate(student)
    if academic_session_id:
        enrollment = session.exec(
            select(Enrollment)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.academic_session_id == academic_session_id,
            )
            .order_by(col(Enrollment.created_at).desc())
        ).first()
        read_student.enrollment = (
            EnrollmentRead.model_validate(enrollment)
            if enrollment is not None
            else None
        )
    return read_student


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
