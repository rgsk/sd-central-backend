import math
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
from models.class_student import ClassStudent

router = APIRouter(
    prefix="/report-cards",
    tags=["report-cards"],
)


@router.post("", response_model=ReportCardRead)
def create_report_card(
    report_card: ReportCardCreate,
    session: Session = Depends(get_session),
):
    class_student = session.get(ClassStudent, report_card.class_student_id)
    if not class_student:
        raise HTTPException(
            status_code=404, detail="Class student not found"
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
            == class_student.academic_class_id,
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
    academic_term_id: UUID | None = Query(default=None),
    academic_session_id: UUID | None = Query(default=None),
    academic_class_id: UUID | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    statement = select(ReportCard)
    count_statement = select(func.count()).select_from(ReportCard)
    id_statement = select(ReportCard.id).distinct()

    join_class_student = academic_class_id is not None
    join_academic_term = academic_session_id is not None

    if join_class_student:
        statement = statement.join(ClassStudent)
        count_statement = count_statement.join(ClassStudent)
        id_statement = id_statement.join(ClassStudent)
    if join_academic_term:
        statement = statement.join(AcademicTerm)
        count_statement = count_statement.join(AcademicTerm)
        id_statement = id_statement.join(AcademicTerm)

    if academic_term_id:
        condition = ReportCard.academic_term_id == academic_term_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
        id_statement = id_statement.where(condition)
    if academic_session_id:
        condition = AcademicTerm.academic_session_id == academic_session_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
        id_statement = id_statement.where(condition)
    if academic_class_id:
        condition = ClassStudent.academic_class_id == academic_class_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
        id_statement = id_statement.where(condition)
    total = session.exec(count_statement).one()
    results = session.exec(
        statement.order_by(col(ReportCard.created_at).desc())
        .offset(offset)
        .limit(limit)
    ).all()
    items: list[ReportCardReadDetail] = [
        ReportCardReadDetail.model_validate(report_card)
        for report_card in results
    ]

    if academic_class_id and items:
        report_card_ids_raw = session.exec(id_statement).all()
        report_card_ids = [
            report_card_id
            for report_card_id in report_card_ids_raw
            if report_card_id is not None
        ]
        percentages_by_id, ranks_by_id = _compute_percentages_and_ranks(
            session,
            report_card_ids,
        )
        for report_card in items:
            if report_card.id in percentages_by_id:
                report_card.overall_percentage = percentages_by_id[
                    report_card.id
                ]
                report_card.rank = ranks_by_id.get(report_card.id)
    return ReportCardListResponse(total=total, items=items)


@router.get("/{report_card_id}", response_model=ReportCardReadDetail)
def get_report_card(
    report_card_id: UUID,
    session: Session = Depends(get_session),
):
    report_card = session.get(ReportCard, report_card_id)
    if not report_card:
        raise HTTPException(status_code=404, detail="Report card not found")
    read_report_card = ReportCardReadDetail.model_validate(report_card)
    class_student = session.get(ClassStudent, report_card.class_student_id)
    if class_student:
        report_card_ids_raw = session.exec(
            select(ReportCard.id)
            .join(ClassStudent)
            .where(
                ClassStudent.academic_class_id
                == class_student.academic_class_id,
                ReportCard.academic_term_id == report_card.academic_term_id,
            )
        ).all()
        report_card_ids = [
            report_card_id
            for report_card_id in report_card_ids_raw
            if report_card_id is not None
        ]
        percentages_by_id, ranks_by_id = _compute_percentages_and_ranks(
            session,
            report_card_ids,
        )
        if report_card_id in percentages_by_id:
            read_report_card.overall_percentage = percentages_by_id[
                report_card_id
            ]
            read_report_card.rank = ranks_by_id.get(report_card_id)
    return read_report_card


def _compute_percentages_and_ranks(
    session: Session, report_card_ids: list[UUID]
) -> tuple[dict[UUID, int], dict[UUID, int]]:
    if not report_card_ids:
        return {}, {}

    subject_total = (
        func.coalesce(ReportCardSubject.notebook, 0)
        + func.coalesce(ReportCardSubject.class_test, 0)
        + func.coalesce(ReportCardSubject.assignment, 0)
        + func.coalesce(ReportCardSubject.mid_term, 0)
        + func.coalesce(ReportCardSubject.final_term, 0)
    )

    totals = session.exec(
        select(
            col(ReportCardSubject.report_card_id),
            func.coalesce(func.sum(subject_total), 0),
            func.count(col(ReportCardSubject.id)),
        )
        .join(
            AcademicClassSubject,
            col(AcademicClassSubject.id)
            == col(ReportCardSubject.academic_class_subject_id),
        )
        .where(
            col(ReportCardSubject.report_card_id).in_(report_card_ids),
            col(AcademicClassSubject.is_additional) == False,
        )
        .group_by(col(ReportCardSubject.report_card_id))
    ).all()

    percentages_by_id: dict[UUID, int] = {}
    for report_card_id, total_marks, subject_count in totals:
        if subject_count:
            percentages_by_id[report_card_id] = math.ceil(
                total_marks / subject_count
            )

    ranks_by_id: dict[UUID, int] = {}
    sorted_items = sorted(
        percentages_by_id.items(), key=lambda item: item[1], reverse=True
    )
    current_rank = 0
    last_percentage = None
    for index, (report_card_id, percentage) in enumerate(
        sorted_items, start=1
    ):
        if percentage != last_percentage:
            current_rank = index
            last_percentage = percentage
        ranks_by_id[report_card_id] = current_rank

    return percentages_by_id, ranks_by_id


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
