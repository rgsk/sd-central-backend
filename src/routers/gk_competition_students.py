from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.gk_competition_student import (GKCompetitionStudent,
                                           GKCompetitionStudentCreate,
                                           GKCompetitionStudentListResponse,
                                           GKCompetitionStudentRead,
                                           GKCompetitionStudentUpdate)

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
    school_name: str | None = Query(default=None),
    class_name: str | None = Query(default=None),
    selected_ids: list[UUID] | None = Query(default=None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    search_value = search.strip() if search else ""
    school_name_value = school_name.strip() if school_name else ""
    class_name_value = class_name.strip() if class_name else ""
    statement = select(GKCompetitionStudent)
    count_statement = select(func.count()).select_from(
        GKCompetitionStudent
    )
    filters = []
    if selected_ids:
        filters.append(col(GKCompetitionStudent.id).in_(selected_ids))
    else:
        if search_value:
            pattern = f"%{search_value}%"
            condition = or_(
                col(GKCompetitionStudent.name).ilike(pattern),
                col(GKCompetitionStudent.roll_no).ilike(pattern),
                col(GKCompetitionStudent.aadhaar_no).ilike(pattern),
            )
            filters.append(condition)
        if school_name_value:
            filters.append(
                col(GKCompetitionStudent.school_name)
                == school_name_value
            )
        if class_name_value:
            filters.append(
                col(GKCompetitionStudent.class_name)
                == class_name_value
            )
    if filters:
        statement = statement.where(*filters)
        count_statement = count_statement.where(*filters)
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


@router.get("/school-options", response_model=list[str])
def list_gk_competition_school_options(
    session: Session = Depends(get_session),
):
    trimmed_school_name = func.trim(col(GKCompetitionStudent.school_name))
    statement = (
        select(trimmed_school_name)
        .distinct()
        .where(
            col(GKCompetitionStudent.school_name).isnot(None),
            trimmed_school_name != "",
        )
        .order_by(trimmed_school_name)
    )
    return session.exec(statement).all()


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
