from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from db import get_session
from models.report_card import (ReportCard, ReportCardCreate, ReportCardRead,
                                ReportCardReadDetail, ReportCardUpdate)

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


@router.get("", response_model=list[ReportCardReadDetail])
def list_report_cards(
    student_id: UUID | None = Query(default=None),
    academic_term_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(ReportCard)
    if student_id:
        statement = statement.where(ReportCard.student_id == student_id)
    if academic_term_id:
        statement = statement.where(
            ReportCard.academic_term_id == academic_term_id
        )
    results = session.exec(statement).all()
    return results


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
