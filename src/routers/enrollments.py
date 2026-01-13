from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, col, select

from db import get_session
from models.academic_class import AcademicClass
from models.academic_session import AcademicSession
from models.enrollment import (Enrollment, EnrollmentCreate,
                               EnrollmentListResponse, EnrollmentRead,
                               EnrollmentUpdate)
from models.student import Student

router = APIRouter(
    prefix="/enrollments",
    tags=["enrollments"],
)


class EnrollmentCountResponse(SQLModel):
    total: int


@router.post("", response_model=EnrollmentRead)
def create_enrollment(
    enrollment: EnrollmentCreate,
    session: Session = Depends(get_session),
):
    student = session.get(Student, enrollment.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    academic_class = session.get(
        AcademicClass, enrollment.academic_class_id
    )
    if not academic_class:
        raise HTTPException(
            status_code=404, detail="Academic class not found"
        )
    if academic_class.academic_session_id != enrollment.academic_session_id:
        raise HTTPException(
            status_code=400,
            detail="Academic session does not match the class session",
        )

    db_enrollment = Enrollment(**enrollment.model_dump())
    session.add(db_enrollment)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Enrollment already exists",
        )
    session.refresh(db_enrollment)
    return db_enrollment


@router.get("", response_model=EnrollmentListResponse)
def list_enrollments(
    student_id: UUID | None = Query(default=None),
    academic_class_id: UUID | None = Query(default=None),
    selected_ids: list[UUID] | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = (
        select(Enrollment)
        .join(
            AcademicSession,
            col(AcademicSession.id)
            == col(Enrollment.academic_session_id),
        )
        .join(Student, col(Student.id) == col(Enrollment.student_id))
    )
    count_statement = select(func.count()).select_from(Enrollment)
    if student_id:
        condition = Enrollment.student_id == student_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_class_id:
        condition = Enrollment.academic_class_id == academic_class_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if selected_ids:
        condition = col(Enrollment.id).in_(selected_ids)
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(
            col(Student.name),
            col(AcademicSession.year),
            col(Enrollment.created_at).desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[EnrollmentRead], results)
    return EnrollmentListResponse(total=total, items=items)


@router.get("/count", response_model=EnrollmentCountResponse)
def count_enrollments(
    academic_class_id: UUID,
    session: Session = Depends(get_session),
):
    statement = select(func.count()).select_from(Enrollment)
    if academic_class_id:
        statement = statement.where(
            Enrollment.academic_class_id == academic_class_id
        )
    total = session.exec(statement).one()
    return EnrollmentCountResponse(total=total)


@router.get("/{enrollment_id}", response_model=EnrollmentRead)
def get_enrollment(
    enrollment_id: UUID,
    session: Session = Depends(get_session),
):
    enrollment = session.get(Enrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=404, detail="Enrollment not found"
        )
    return enrollment


@router.patch("/{enrollment_id}", response_model=EnrollmentRead)
def partial_update_enrollment(
    enrollment_id: UUID,
    enrollment: EnrollmentUpdate,
    session: Session = Depends(get_session),
):
    db_enrollment = session.get(Enrollment, enrollment_id)
    if not db_enrollment:
        raise HTTPException(
            status_code=404, detail="Enrollment not found"
        )

    update_data = enrollment.model_dump(exclude_unset=True)
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
            "academic_session_id", db_enrollment.academic_session_id
        )
        next_class = academic_class or session.get(
            AcademicClass, db_enrollment.academic_class_id
        )
        if next_class and next_class.academic_session_id != next_session_id:
            raise HTTPException(
                status_code=400,
                detail="Academic session does not match the class session",
            )

    for key, value in update_data.items():
        setattr(db_enrollment, key, value)

    session.add(db_enrollment)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Enrollment already exists",
        )
    session.refresh(db_enrollment)
    return db_enrollment


@router.delete("/{enrollment_id}")
def delete_enrollment(
    enrollment_id: UUID,
    session: Session = Depends(get_session),
):
    db_enrollment = session.get(Enrollment, enrollment_id)
    if not db_enrollment:
        raise HTTPException(
            status_code=404, detail="Enrollment not found"
        )
    session.delete(db_enrollment)
    session.commit()
    return {"message": "Enrollment deleted"}
