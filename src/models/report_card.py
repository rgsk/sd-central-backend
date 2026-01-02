from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_term import AcademicTermRead
from models.student import StudentRead

if TYPE_CHECKING:
    from models.academic_term import AcademicTerm
    from models.report_card_subject import ReportCardSubject
    from models.student import Student


class ReportCardDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ReportCardBase(SQLModel):
    student_id: UUID = Field(
        foreign_key="students.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    academic_term_id: UUID = Field(
        foreign_key="academic_terms.id",
        sa_type=PG_UUID(as_uuid=True),
    )


class ReportCard(ReportCardBase, ReportCardDB, table=True):
    __tablename__ = "report_cards"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "academic_term_id",
            name="uq_report_card_student_term",
        ),
    )
    student: Optional["Student"] = Relationship(back_populates="report_cards")
    academic_term: Optional["AcademicTerm"] = Relationship(
        back_populates="report_cards"
    )
    report_card_subjects: list["ReportCardSubject"] = Relationship(
        back_populates="report_card"
    )
    pass


class ReportCardCreate(ReportCardBase):
    pass


class ReportCardUpdate(SQLModel):
    student_id: Optional[UUID] = None
    academic_term_id: Optional[UUID] = None


class ReportCardId(SQLModel):
    id: UUID


class ReportCardRead(ReportCardBase, ReportCardId):
    created_at: datetime


class ReportCardReadDetail(ReportCardRead):
    student: Optional[StudentRead] = None
    academic_term: Optional[AcademicTermRead] = None
