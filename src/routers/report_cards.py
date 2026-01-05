from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class_subject import AcademicClassSubject
from models.academic_term import AcademicTerm
from models.report_card import (ReportCard, ReportCardCreate, ReportCardRead,
                                ReportCardListResponse, ReportCardReadDetail,
                                ReportCardUpdate)
from models.report_card_subject import ReportCardSubject
from models.student import Student

router = APIRouter(
    prefix="/report-cards",
    tags=["report-cards"],
)


@router.post("", response_model=ReportCardRead)
def create_report_card(
    report_card: ReportCardCreate,
    session: Session = Depends(get_session),
):
    student = session.get(Student, report_card.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if not student.academic_class_id:
        raise HTTPException(
            status_code=400,
            detail="Student must be assigned to a class",
        )
    academic_term = session.get(AcademicTerm, report_card.academic_term_id)
    if not academic_term:
        raise HTTPException(status_code=404, detail="Academic term not found")

    db_report_card = ReportCard(**report_card.model_dump())
    session.add(db_report_card)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Report card already exists"
        )

    class_subjects_raw = session.exec(
        select(AcademicClassSubject.id).where(
            AcademicClassSubject.academic_class_id
            == student.academic_class_id,
            AcademicClassSubject.academic_term_id
            == report_card.academic_term_id,
        )
    ).all()
    if db_report_card.id is None:
        raise HTTPException(
            status_code=500, detail="Report card ID was not generated"
        )
    class_subject_ids = [
        class_subject_id
        for class_subject_id in class_subjects_raw
        if class_subject_id is not None
    ]
    for class_subject_id in class_subject_ids:
        session.add(
            ReportCardSubject(
                report_card_id=db_report_card.id,
                academic_class_subject_id=class_subject_id,
            )
        )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409, detail="Report card subjects already exist"
        )
    session.refresh(db_report_card)
    return db_report_card


@router.get("", response_model=ReportCardListResponse)
def list_report_cards(
    student_id: UUID | None = Query(default=None),
    academic_term_id: UUID | None = Query(default=None),
    academic_session_id: UUID | None = Query(default=None),
    academic_class_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = select(ReportCard)
    count_statement = select(func.count()).select_from(ReportCard)
    if student_id:
        condition = ReportCard.student_id == student_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_term_id:
        condition = ReportCard.academic_term_id == academic_term_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_session_id:
        statement = statement.join(AcademicTerm)
        count_statement = count_statement.join(AcademicTerm)
        condition = AcademicTerm.academic_session_id == academic_session_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_class_id:
        statement = statement.join(Student)
        count_statement = count_statement.join(Student)
        condition = Student.academic_class_id == academic_class_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(col(ReportCard.created_at).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[ReportCardReadDetail], results)
    return ReportCardListResponse(total=total, items=items)


@router.get("/{report_card_id}", response_model=ReportCardReadDetail)
def get_report_card(
    report_card_id: UUID,
    session: Session = Depends(get_session),
):
    report_card = session.get(ReportCard, report_card_id)
    if not report_card:
        raise HTTPException(status_code=404, detail="Report card not found")
    return report_card


@router.patch("/{report_card_id}", response_model=ReportCardRead)
def partial_update_report_card(
    report_card_id: UUID,
    report_card: ReportCardUpdate,
    session: Session = Depends(get_session),
):
    db_report_card = session.get(ReportCard, report_card_id)
    if not db_report_card:
        raise HTTPException(status_code=404, detail="Report card not found")

    update_data = report_card.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_report_card, key, value)

    session.add(db_report_card)
    session.commit()
    session.refresh(db_report_card)
    return db_report_card


@router.delete("/{report_card_id}")
def delete_report_card(
    report_card_id: UUID,
    session: Session = Depends(get_session),
):
    db_report_card = session.get(ReportCard, report_card_id)
    if not db_report_card:
        raise HTTPException(status_code=404, detail="Report card not found")
    session.delete(db_report_card)
    session.commit()
    return {"message": "Report card deleted"}
