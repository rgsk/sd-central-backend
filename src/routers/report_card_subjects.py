from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, col, select

from db import get_session
from models.report_card_subject import (
    ReportCardSubject,
    ReportCardSubjectCreate,
    ReportCardSubjectListResponse,
    ReportCardSubjectRead,
    ReportCardSubjectUpdate,
)

router = APIRouter(
    prefix="/report-card-subjects",
    tags=["report-card-subjects"],
)


@router.post("", response_model=ReportCardSubjectRead)
def create_report_card_subject(
    report_card_subject: ReportCardSubjectCreate,
    session: Session = Depends(get_session),
):
    db_report_card_subject = ReportCardSubject(
        **report_card_subject.model_dump()
    )
    session.add(db_report_card_subject)
    session.commit()
    session.refresh(db_report_card_subject)
    return db_report_card_subject


@router.get("", response_model=ReportCardSubjectListResponse)
def list_report_card_subjects(
    report_card_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = select(ReportCardSubject)
    count_statement = select(func.count()).select_from(ReportCardSubject)
    if report_card_id:
        condition = ReportCardSubject.report_card_id == report_card_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if subject_id:
        condition = ReportCardSubject.subject_id == subject_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(col(ReportCardSubject.created_at))
        .offset(offset)
        .limit(limit)
    ).all()
    items = cast(list[ReportCardSubjectRead], results)
    return ReportCardSubjectListResponse(total=total, items=items)


@router.get("/{report_card_subject_id}", response_model=ReportCardSubjectRead)
def get_report_card_subject(
    report_card_subject_id: UUID,
    session: Session = Depends(get_session),
):
    report_card_subject = session.get(
        ReportCardSubject, report_card_subject_id
    )
    if not report_card_subject:
        raise HTTPException(
            status_code=404, detail="Report card subject not found"
        )
    return report_card_subject


@router.patch("/{report_card_subject_id}", response_model=ReportCardSubjectRead)
def partial_update_report_card_subject(
    report_card_subject_id: UUID,
    report_card_subject: ReportCardSubjectUpdate,
    session: Session = Depends(get_session),
):
    db_report_card_subject = session.get(
        ReportCardSubject, report_card_subject_id
    )
    if not db_report_card_subject:
        raise HTTPException(
            status_code=404, detail="Report card subject not found"
        )

    update_data = report_card_subject.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_report_card_subject, key, value)

    session.add(db_report_card_subject)
    session.commit()
    session.refresh(db_report_card_subject)
    return db_report_card_subject


@router.delete("/{report_card_subject_id}")
def delete_report_card_subject(
    report_card_subject_id: UUID,
    session: Session = Depends(get_session),
):
    db_report_card_subject = session.get(
        ReportCardSubject, report_card_subject_id
    )
    if not db_report_card_subject:
        raise HTTPException(
            status_code=404, detail="Report card subject not found"
        )
    session.delete(db_report_card_subject)
    session.commit()
    return {"message": "Report card subject deleted"}
