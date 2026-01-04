from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, col, select

from db import get_session
from models.academic_term import AcademicTerm
from models.report_card import (ReportCard, ReportCardCreate, ReportCardRead,
                                ReportCardListResponse, ReportCardReadDetail,
                                ReportCardUpdate)
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
    db_report_card = ReportCard(**report_card.model_dump())
    session.add(db_report_card)
    session.commit()
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
