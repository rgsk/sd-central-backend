from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from db import get_session
from models.report_card_subject import (
    ReportCardSubject,
    ReportCardSubjectCreate,
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


@router.get("", response_model=list[ReportCardSubjectRead])
def list_report_card_subjects(
    report_card_id: UUID | None = Query(default=None),
    subject_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
):
    statement = select(ReportCardSubject)
    if report_card_id:
        statement = statement.where(
            ReportCardSubject.report_card_id == report_card_id
        )
    if subject_id:
        statement = statement.where(
            ReportCardSubject.subject_id == subject_id
        )
    results = session.exec(statement).all()
    return results


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
