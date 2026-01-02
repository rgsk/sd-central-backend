from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.report_card import ReportCard
    from models.subject import Subject


class ReportCardSubjectDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ReportCardSubjectBase(SQLModel):
    report_card_id: UUID = Field(
        foreign_key="report_cards.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    subject_id: UUID = Field(
        foreign_key="subjects.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    mid_term: Optional[int] = None
    notebook: Optional[int] = None
    assignment: Optional[int] = None
    class_test: Optional[int] = None
    final_term: Optional[int] = None
    final_marks: Optional[int] = None


class ReportCardSubject(
    ReportCardSubjectBase, ReportCardSubjectDB, table=True
):
    __tablename__ = "report_card_subjects"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "report_card_id",
            "subject_id",
            name="uq_report_card_subject",
        ),
    )
    report_card: Optional["ReportCard"] = Relationship(
        back_populates="report_card_subjects"
    )
    subject: Optional["Subject"] = Relationship(
        back_populates="report_card_subjects"
    )
    pass


class ReportCardSubjectCreate(ReportCardSubjectBase):
    pass


class ReportCardSubjectUpdate(SQLModel):
    report_card_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    mid_term: Optional[int] = None
    notebook: Optional[int] = None
    assignment: Optional[int] = None
    class_test: Optional[int] = None
    final_term: Optional[int] = None
    final_marks: Optional[int] = None


class ReportCardSubjectId(SQLModel):
    id: UUID


class ReportCardSubjectRead(
    ReportCardSubjectBase, ReportCardSubjectId
):
    created_at: datetime


class ReportCardSubjectListResponse(SQLModel):
    total: int
    items: list[ReportCardSubjectRead]
