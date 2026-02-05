from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.gk_competition_student import (
    GKCompetitionStudent,
    GKCompetitionStudentCreate,
    GKCompetitionStudentListResponse,
    GKCompetitionStudentRead,
    GKCompetitionStudentUpdate,
)

router = APIRouter(
    prefix="/gk-competition-students",
    tags=["gk-competition-students"],
)


@router.post("", response_model=GKCompetitionStudentRead)
def create_gk_competition_student(
    student: GKCompetitionStudentCreate,
    session: Session = Depends(get_session),
):
    db_student = GKCompetitionStudent(**student.model_dump())
    session.add(db_student)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Aadhaar or roll number already exists",
        )
    session.refresh(db_student)
    return db_student


@router.get("", response_model=GKCompetitionStudentListResponse)
def list_gk_competition_students(
    session: Session = Depends(get_session),
    search: str | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    search_value = search.strip() if search else ""
    statement = select(GKCompetitionStudent)
    count_statement = select(func.count()).select_from(
        GKCompetitionStudent
    )
    if search_value:
        pattern = f"%{search_value}%"
        condition = or_(
            col(GKCompetitionStudent.name).ilike(pattern),
            col(GKCompetitionStudent.roll_no).ilike(pattern),
            col(GKCompetitionStudent.father_name).ilike(pattern),
            col(GKCompetitionStudent.mother_name).ilike(pattern),
            col(GKCompetitionStudent.class_name).ilike(pattern),
            col(GKCompetitionStudent.school_name).ilike(pattern),
            col(GKCompetitionStudent.school_address).ilike(pattern),
            col(GKCompetitionStudent.aadhaar_no).ilike(pattern),
            col(GKCompetitionStudent.group).ilike(pattern),
            col(GKCompetitionStudent.paper_medium).ilike(pattern),
            col(GKCompetitionStudent.exam_center).ilike(pattern),
            col(GKCompetitionStudent.contact_no).ilike(pattern),
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    statement = (
        statement
        .order_by(
            col(GKCompetitionStudent.name),
            col(GKCompetitionStudent.created_at).desc(),
        )
        .offset(offset)
        .limit(limit)
    )
    items = cast(
        list[GKCompetitionStudentRead],
        session.exec(statement).all(),
    )
    return GKCompetitionStudentListResponse(total=total, items=items)


@router.get("/find", response_model=GKCompetitionStudentRead)
def find_gk_competition_student(
    session: Session = Depends(get_session),
    aadhaar_no: str | None = Query(default=None),
    roll_no: str | None = Query(default=None),
):
    aadhaar_value = aadhaar_no.strip() if aadhaar_no else ""
    roll_value = roll_no.strip() if roll_no else ""
    if not aadhaar_value and not roll_value:
        raise HTTPException(
            status_code=400,
            detail="aadhaarNo or rollNo is required",
        )
    conditions = []
    if aadhaar_value:
        conditions.append(
            col(GKCompetitionStudent.aadhaar_no) == aadhaar_value
        )
    if roll_value:
        conditions.append(
            col(GKCompetitionStudent.roll_no) == roll_value
        )
    student = session.exec(
        select(GKCompetitionStudent).where(or_(*conditions))
    ).first()
    if not student:
        raise HTTPException(
            status_code=404, detail="Student not found"
        )
    return student


@router.get("/{gk_competition_student_id}",
            response_model=GKCompetitionStudentRead)
def get_gk_competition_student(
    gk_competition_student_id: UUID,
    session: Session = Depends(get_session),
):
    student = session.get(
        GKCompetitionStudent, gk_competition_student_id
    )
    if not student:
        raise HTTPException(
            status_code=404, detail="Student not found"
        )
    return student


@router.patch("/{gk_competition_student_id}",
              response_model=GKCompetitionStudentRead)
def partial_update_gk_competition_student(
    gk_competition_student_id: UUID,
    student: GKCompetitionStudentUpdate,
    session: Session = Depends(get_session),
):
    db_student = session.get(
        GKCompetitionStudent, gk_competition_student_id
    )
    if not db_student:
        raise HTTPException(
            status_code=404, detail="Student not found"
        )

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
            detail="Aadhaar or roll number already exists",
        )
    session.refresh(db_student)
    return db_student


@router.delete("/{gk_competition_student_id}")
def delete_gk_competition_student(
    gk_competition_student_id: UUID,
    session: Session = Depends(get_session),
):
    db_student = session.get(
        GKCompetitionStudent, gk_competition_student_id
    )
    if not db_student:
        raise HTTPException(
            status_code=404, detail="Student not found"
        )
    session.delete(db_student)
    session.commit()
    return {"message": "Student deleted"}
