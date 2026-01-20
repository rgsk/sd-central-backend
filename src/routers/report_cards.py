import math
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import case, func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, col, select

from db import get_session
from models.academic_class_subject import AcademicClassSubject
from models.academic_term import AcademicTerm, AcademicTermType
from models.enrollment import Enrollment, EnrollmentReadRaw
from models.report_card import (ReportCard, ReportCardCreate,
                                ReportCardListResponse, ReportCardRead,
                                ReportCardReadDetail,
                                ReportCardReadDetailWithSubjects,
                                ReportCardUpdate)
from models.report_card_subject import ReportCardSubject, ReportCardSubjectRead
from models.student import Student
from routers.report_card_subjects import REPORT_CARD_SUBJECT_ORDER_BY

router = APIRouter(
    prefix="/report-cards",
    tags=["report-cards"],
)


class ReportCardGenerationResponse(SQLModel):
    total: int


@router.post("", response_model=ReportCardRead)
def create_report_card(
    report_card: ReportCardCreate,
    session: Session = Depends(get_session),
):
    enrollment = session.get(Enrollment, report_card.enrollment_id)
    if not enrollment:
        raise HTTPException(
            status_code=404, detail="Enrollment not found"
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
            == enrollment.academic_class_id,
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
    selected_ids: list[UUID] | None = Query(default=None),
    search: str | None = Query(default=None),
    session: Session = Depends(get_session),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str | None = Query(default=None),
    sort_dir: str | None = Query(default="desc"),
):
    statement = select(ReportCard)
    count_statement = select(func.count()).select_from(ReportCard)
    id_statement = select(ReportCard.id).distinct()

    search_value = search.strip() if search else ""
    join_enrollment = academic_class_id is not None or bool(search_value)
    join_academic_term = academic_session_id is not None
    join_student = academic_class_id is not None or bool(search_value)

    if join_enrollment:
        statement = statement.join(Enrollment)
        count_statement = count_statement.join(Enrollment)
        id_statement = id_statement.join(Enrollment)
    if join_academic_term:
        statement = statement.join(AcademicTerm)
        count_statement = count_statement.join(AcademicTerm)
        id_statement = id_statement.join(AcademicTerm)
    if join_student:
        statement = statement.join(
            Student,
            col(Student.id) == col(Enrollment.student_id),
        )
        count_statement = count_statement.join(
            Student,
            col(Student.id) == col(Enrollment.student_id),
        )
        id_statement = id_statement.join(
            Student,
            col(Student.id) == col(Enrollment.student_id),
        )

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
        condition = Enrollment.academic_class_id == academic_class_id
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
        id_statement = id_statement.where(condition)
    if search_value:
        condition = or_(
            col(Student.registration_no).ilike(f"%{search_value}%"),
            col(Student.name).ilike(f"%{search_value}%"),
        )
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
        id_statement = id_statement.where(condition)
    if selected_ids:
        condition = col(ReportCard.id).in_(selected_ids)
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)
        id_statement = id_statement.where(condition)
    total = session.exec(count_statement).one()
    order_by_clauses = [col(ReportCard.created_at).desc()]
    if academic_class_id:
        order_by_clauses = [
            col(Student.name),
            col(ReportCard.created_at).desc(),
        ]
    normalized_sort_by = sort_by.lower() if sort_by else None
    normalized_sort_dir = (sort_dir or "desc").lower()
    should_sort_by_rank = (
        normalized_sort_by == "rank"
        and academic_class_id
        and academic_term_id
    )
    should_sort_by_percentage = (
        normalized_sort_by == "percentage"
        and academic_class_id
        and academic_term_id
    )
    sort_desc = normalized_sort_dir != "asc"

    items: list[ReportCardReadDetail] = []
    if not should_sort_by_rank and not should_sort_by_percentage:
        results = session.exec(
            statement.order_by(*order_by_clauses)
            .offset(offset)
            .limit(limit)
        ).all()
        items = [
            ReportCardReadDetail.model_validate(report_card)
            for report_card in results
        ]

    report_card_ids_raw = session.exec(id_statement).all()
    report_card_ids = [
        report_card_id
        for report_card_id in report_card_ids_raw
        if report_card_id is not None
    ]
    percentages_by_id: dict[UUID, int] = {}
    ranks_by_id: dict[UUID, int] = {}
    if academic_class_id and academic_term_id:
        academic_term = session.get(AcademicTerm, academic_term_id)
        if academic_term:
            percentages_by_id, ranks_by_id = (
                compute_percentages_and_ranks_for_term(
                    session,
                    academic_term,
                    academic_class_id,
                )
            )
        for report_card in items:
            if report_card.id in percentages_by_id:
                report_card.overall_percentage = percentages_by_id[
                    report_card.id
                ]
                report_card.rank = ranks_by_id.get(report_card.id)

    if should_sort_by_rank or should_sort_by_percentage:
        def sort_value(value: int | None) -> float:
            if value is None:
                return float("-inf") if sort_desc else float("inf")
            return float(value)

        def sort_key(report_card_id: UUID) -> tuple[float, float, UUID]:
            rank_value = sort_value(ranks_by_id.get(report_card_id))
            percentage_value = sort_value(
                percentages_by_id.get(report_card_id)
            )
            if should_sort_by_rank:
                return (rank_value, percentage_value, report_card_id)
            return (percentage_value, rank_value, report_card_id)

        ordered_ids = sorted(
            report_card_ids, key=sort_key, reverse=sort_desc
        )
        page_ids = ordered_ids[offset: offset + limit]
        if not page_ids:
            return ReportCardListResponse(total=total, items=[])

        order_case = case(
            {report_card_id: index for index,
                report_card_id in enumerate(page_ids)},
            value=col(ReportCard.id),
        )
        results = session.exec(
            statement.where(col(ReportCard.id).in_(
                page_ids)).order_by(order_case)
        ).all()
        items = [
            ReportCardReadDetail.model_validate(report_card)
            for report_card in results
        ]
        for report_card in items:
            if report_card.id in percentages_by_id:
                report_card.overall_percentage = percentages_by_id[
                    report_card.id
                ]
                report_card.rank = ranks_by_id.get(report_card.id)

    report_cards_with_subjects: list[ReportCardReadDetailWithSubjects] = []
    if items:
        item_ids = [report_card.id for report_card in items]
        subjects = session.exec(
            select(ReportCardSubject)
            .join(
                AcademicClassSubject,
                col(AcademicClassSubject.id)
                == col(ReportCardSubject.academic_class_subject_id),
            )
            .where(col(ReportCardSubject.report_card_id).in_(item_ids))
            .order_by(
                col(ReportCardSubject.report_card_id),
                *REPORT_CARD_SUBJECT_ORDER_BY,
            )
        ).all()
        subjects_by_report_card: dict[
            UUID, list[ReportCardSubjectRead]
        ] = {report_card_id: [] for report_card_id in item_ids}
        for subject in subjects:
            subjects_by_report_card[subject.report_card_id].append(
                ReportCardSubjectRead.model_validate(subject)
            )
        report_cards_with_subjects = [
            ReportCardReadDetailWithSubjects(
                **rc.model_dump(),
                report_card_subjects=subjects_by_report_card.get(
                    rc.id, []
                ),
            )
            for rc in items
        ]

    return ReportCardListResponse(total=total, items=report_cards_with_subjects)


class ReportCardGenerationRequest(SQLModel):
    academic_class_id: UUID
    academic_term_id: UUID


@router.post("/generate", response_model=ReportCardGenerationResponse)
def generate_report_cards(
    payload: ReportCardGenerationRequest = Body(...),
    session: Session = Depends(get_session),
):
    academic_term = session.get(AcademicTerm, payload.academic_term_id)
    if not academic_term:
        raise HTTPException(
            status_code=404, detail="Academic term not found"
        )

    enrollments = session.exec(
        select(Enrollment)
        .where(
            Enrollment.academic_class_id == payload.academic_class_id,
            Enrollment.academic_session_id
            == academic_term.academic_session_id,
        )
    ).all()
    if len(enrollments) == 0:
        return ReportCardGenerationResponse(total=0)

    enrollments = [
        EnrollmentReadRaw.model_validate(enrollment)
        for enrollment in enrollments
    ]

    enrollment_ids = [enrollment.id for enrollment in enrollments]
    existing_enrollment_ids_raw = session.exec(
        select(ReportCard.enrollment_id)
        .where(
            ReportCard.academic_term_id == payload.academic_term_id,
            col(ReportCard.enrollment_id).in_(enrollment_ids),
        )
    ).all()
    existing_enrollment_ids = {
        enrollment_id
        for enrollment_id in existing_enrollment_ids_raw
    }

    created = 0
    for enrollment in enrollments:
        if enrollment.id in existing_enrollment_ids:
            continue

        try:
            create_report_card(
                ReportCardCreate(
                    enrollment_id=enrollment.id,
                    academic_term_id=payload.academic_term_id,
                ),
                session,
            )
        except HTTPException as exc:
            if exc.status_code == 409:
                continue
            raise
        created += 1

    return ReportCardGenerationResponse(total=created)


def populate_rank_and_percentage(
    report_card: ReportCardReadDetail,
    session: Session = Depends(get_session),
):
    enrollment = session.get(Enrollment, report_card.enrollment_id)
    academic_term = session.get(AcademicTerm, report_card.academic_term_id)
    if enrollment and academic_term:
        percentages_by_id, ranks_by_id = (
            compute_percentages_and_ranks_for_term(
                session,
                academic_term,
                enrollment.academic_class_id,
            )
        )
        if report_card.id in percentages_by_id:
            report_card.overall_percentage = percentages_by_id[
                report_card.id
            ]
            report_card.rank = ranks_by_id.get(report_card.id)


@router.get("/{report_card_id}", response_model=ReportCardReadDetail)
def get_report_card(
    report_card_id: UUID,
    session: Session = Depends(get_session),
):
    report_card = session.get(ReportCard, report_card_id)
    if not report_card:
        raise HTTPException(status_code=404, detail="Report card not found")
    read_report_card = ReportCardReadDetail.model_validate(report_card)
    populate_rank_and_percentage(read_report_card, session)
    return read_report_card


def _compute_totals_by_report_card(
    session: Session,
    report_card_ids: list[UUID],
    term_type: AcademicTermType | None = None,
) -> dict[UUID, tuple[int, int]]:
    if not report_card_ids:
        return {}

    if term_type == AcademicTermType.QUARTERLY:
        subject_total = func.coalesce(ReportCardSubject.final_marks, 0)
    else:
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

    totals_by_id: dict[UUID, tuple[int, int]] = {}
    for report_card_id, total_marks, subject_count in totals:
        totals_by_id[report_card_id] = (total_marks, subject_count)
    return totals_by_id


def _compute_percentages_and_ranks_from_totals(
    totals_by_id: dict[UUID, tuple[int, int]]
) -> tuple[dict[UUID, int], dict[UUID, int]]:
    percentages_by_id: dict[UUID, int] = {}
    for report_card_id, (total_marks, subject_count) in totals_by_id.items():
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


def _compute_percentages_and_ranks(
    session: Session,
    report_card_ids: list[UUID],
    term_type: AcademicTermType | None = None,
) -> tuple[dict[UUID, int], dict[UUID, int]]:
    totals_by_id = _compute_totals_by_report_card(
        session,
        report_card_ids,
        term_type,
    )
    return _compute_percentages_and_ranks_from_totals(totals_by_id)


def compute_percentages_and_ranks_for_term(
    session: Session,
    academic_term: AcademicTerm,
    academic_class_id: UUID,
) -> tuple[dict[UUID, int], dict[UUID, int]]:
    report_cards_raw = session.exec(
        select(ReportCard.id, ReportCard.enrollment_id)
        .join(Enrollment)
        .where(
            Enrollment.academic_class_id == academic_class_id,
            ReportCard.academic_term_id == academic_term.id,
        )
    ).all()
    report_cards = [
        (report_card_id, enrollment_id)
        for report_card_id, enrollment_id in report_cards_raw
        if report_card_id is not None and enrollment_id is not None
    ]
    report_card_ids = [
        report_card_id for report_card_id, _ in report_cards
    ]
    if academic_term.term_type != AcademicTermType.ANNUAL:
        return _compute_percentages_and_ranks(
            session,
            report_card_ids,
            academic_term.term_type,
        )

    annual_totals_by_id = _compute_totals_by_report_card(
        session,
        report_card_ids,
        academic_term.term_type,
    )
    half_yearly_term = session.exec(
        select(AcademicTerm).where(
            AcademicTerm.academic_session_id
            == academic_term.academic_session_id,
            AcademicTerm.term_type == AcademicTermType.HALF_YEARLY,
        )
    ).first()
    if not half_yearly_term:
        return _compute_percentages_and_ranks_from_totals(
            annual_totals_by_id
        )

    enrollment_ids = [
        enrollment_id for _, enrollment_id in report_cards
    ]
    half_yearly_report_cards_raw = session.exec(
        select(ReportCard.id, ReportCard.enrollment_id).where(
            ReportCard.academic_term_id == half_yearly_term.id,
            col(ReportCard.enrollment_id).in_(enrollment_ids),
        )
    ).all()
    half_yearly_report_card_ids_by_enrollment = {
        enrollment_id: report_card_id
        for report_card_id, enrollment_id in half_yearly_report_cards_raw
        if report_card_id is not None and enrollment_id is not None
    }
    half_yearly_totals_by_id = _compute_totals_by_report_card(
        session,
        list(half_yearly_report_card_ids_by_enrollment.values()),
        half_yearly_term.term_type,
    )

    combined_totals_by_id: dict[UUID, tuple[int, int]] = {}
    for annual_report_card_id, enrollment_id in report_cards:
        annual_total, annual_count = annual_totals_by_id.get(
            annual_report_card_id, (0, 0)
        )
        half_yearly_report_card_id = (
            half_yearly_report_card_ids_by_enrollment.get(enrollment_id)
        )
        half_yearly_total, half_yearly_count = (
            half_yearly_totals_by_id.get(
                half_yearly_report_card_id, (0, 0)
            )
            if half_yearly_report_card_id
            else (0, 0)
        )
        total_marks = annual_total + half_yearly_total
        subject_count = annual_count + half_yearly_count
        if subject_count:
            combined_totals_by_id[annual_report_card_id] = (
                total_marks,
                subject_count,
            )

    return _compute_percentages_and_ranks_from_totals(
        combined_totals_by_id
    )


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
