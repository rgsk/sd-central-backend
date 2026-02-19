from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, col, select

from db import get_session
from models.academic_class_subject import AcademicClassSubject
from models.academic_class_subject_term import AcademicClassSubjectTerm
from models.academic_term import AcademicTerm, AcademicTermType
from models.enrollment import Enrollment
from models.report_card import ReportCard
from models.report_card_subject import (ReportCardSubject,
                                        ReportCardSubjectCreate,
                                        ReportCardSubjectListResponse,
                                        ReportCardSubjectRead,
                                        ReportCardSubjectUpdate)

router = APIRouter(
    prefix="/report-card-subjects",
    tags=["report-card-subjects"],
)


REPORT_CARD_SUBJECT_ORDER_BY = (
    col(AcademicClassSubject.is_additional).asc(),
    col(AcademicClassSubject.position).asc(),
    col(ReportCardSubject.created_at).desc(),
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
    academic_class_subject_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
):
    statement = select(ReportCardSubject)
    count_statement = select(func.count()).select_from(ReportCardSubject)
    if report_card_id:
        condition = ReportCardSubject.report_card_id == report_card_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    if academic_class_subject_id:
        condition = (
            ReportCardSubject.academic_class_subject_id
            == academic_class_subject_id
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.join(
            AcademicClassSubject,
            col(AcademicClassSubject.id)
            == col(ReportCardSubject.academic_class_subject_id),
        )
        .order_by(*REPORT_CARD_SUBJECT_ORDER_BY)
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

    # update highest and average marks for class subject

    report_card = session.get(
        ReportCard, db_report_card_subject.report_card_id
    )

    if report_card:
        class_subject = session.get(
            AcademicClassSubject,
            db_report_card_subject.academic_class_subject_id,
        )
        if class_subject:
            academic_term = session.get(
                AcademicTerm, report_card.academic_term_id
            )
            use_final_only = (
                academic_term is not None
                and academic_term.term_type == AcademicTermType.QUARTERLY
            ) or class_subject.is_additional
            if use_final_only:
                total_expr = func.coalesce(
                    ReportCardSubject.final_marks, 0
                )
            else:
                total_expr = (
                    func.coalesce(ReportCardSubject.mid_term, 0)
                    + func.coalesce(ReportCardSubject.notebook, 0)
                    + func.coalesce(ReportCardSubject.assignment, 0)
                    + func.coalesce(ReportCardSubject.class_test, 0)
                    + func.coalesce(ReportCardSubject.final_term, 0)
                )

            max_total, avg_total = session.exec(
                select(func.max(total_expr), func.avg(total_expr))
                .select_from(ReportCardSubject)
                .join(
                    ReportCard,
                    col(ReportCard.id)
                    == col(ReportCardSubject.report_card_id),
                )
                .join(
                    Enrollment,
                    col(Enrollment.id)
                    == col(ReportCard.enrollment_id),
                )
                .where(
                    ReportCardSubject.academic_class_subject_id
                    == db_report_card_subject.academic_class_subject_id,
                    ReportCard.academic_term_id
                    == report_card.academic_term_id,
                    Enrollment.academic_class_id
                    == class_subject.academic_class_id,
                )
            ).one()

            class_subject_term = session.exec(
                select(AcademicClassSubjectTerm).where(
                    AcademicClassSubjectTerm.academic_class_subject_id
                    == db_report_card_subject.academic_class_subject_id,
                    AcademicClassSubjectTerm.academic_term_id
                    == report_card.academic_term_id,
                )
            ).one_or_none()
            if not class_subject_term:
                class_subject_term = AcademicClassSubjectTerm(
                    academic_class_subject_id=(
                        db_report_card_subject.academic_class_subject_id
                    ),
                    academic_term_id=report_card.academic_term_id,
                )
            class_subject_term.highest_marks = (
                int(max_total) if max_total is not None else None
            )
            class_subject_term.average_marks = (
                int(round(avg_total)) if avg_total is not None else None
            )
            session.add(class_subject_term)
            session.commit()

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
