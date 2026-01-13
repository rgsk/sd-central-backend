from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_term import AcademicTermRead
from models.enrollment import EnrollmentRead
from models.report_card_subject import ReportCardSubjectRead

if TYPE_CHECKING:
    from models.academic_term import AcademicTerm
    from models.enrollment import Enrollment
    from models.report_card_subject import ReportCardSubject


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


class ReportCardGrade(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"


class ReportCardResult(str, Enum):
    PROMOTED = "promoted"
    PASSED = "passed"
    NEED_IMPROVEMENT = "need_improvement"
    RESULT_WITHHELD = "result_withheld"


class ReportCardBase(SQLModel):
    enrollment_id: UUID = Field(
        foreign_key="enrollments.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    academic_term_id: UUID = Field(
        foreign_key="academic_terms.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    work_education_grade: Optional[ReportCardGrade] = None
    art_education_grade: Optional[ReportCardGrade] = None
    physical_education_grade: Optional[ReportCardGrade] = None
    behaviour_grade: Optional[ReportCardGrade] = None
    attendance_present: Optional[int] = None
    result: Optional[ReportCardResult] = None


class ReportCard(ReportCardBase, ReportCardDB, table=True):
    __tablename__ = "report_cards"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "enrollment_id",
            "academic_term_id",
            name="uq_report_card_enrollment_term",
        ),
    )
    enrollment: Optional["Enrollment"] = Relationship(
        back_populates="report_cards"
    )
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
    enrollment_id: Optional[UUID] = None
    academic_term_id: Optional[UUID] = None
    work_education_grade: Optional[ReportCardGrade] = None
    art_education_grade: Optional[ReportCardGrade] = None
    physical_education_grade: Optional[ReportCardGrade] = None
    behaviour_grade: Optional[ReportCardGrade] = None
    attendance_present: Optional[int] = None
    result: Optional[ReportCardResult] = None


class ReportCardId(SQLModel):
    id: UUID


class ReportCardRead(ReportCardBase, ReportCardId):
    created_at: datetime


class ReportCardReadDetail(ReportCardRead):
    enrollment: Optional[EnrollmentRead] = None
    academic_term: Optional[AcademicTermRead] = None
    report_card_subjects: list[ReportCardSubjectRead] = []
    overall_percentage: Optional[int] = None
    rank: Optional[int] = None


class ReportCardListResponse(SQLModel):
    total: int
    items: list[ReportCardReadDetail]
