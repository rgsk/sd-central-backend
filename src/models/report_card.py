from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_term import AcademicTermRead
from models.class_student import ClassStudentRead

if TYPE_CHECKING:
    from models.academic_term import AcademicTerm
    from models.report_card_subject import ReportCardSubject
    from models.class_student import ClassStudent


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
    class_student_id: UUID = Field(
        foreign_key="class_students.id",
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
            "class_student_id",
            "academic_term_id",
            name="uq_report_card_class_student_term",
        ),
    )
    class_student: Optional["ClassStudent"] = Relationship(
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
    class_student_id: Optional[UUID] = None
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
    class_student: Optional[ClassStudentRead] = None
    academic_term: Optional[AcademicTermRead] = None


class ReportCardListResponse(SQLModel):
    total: int
    items: list[ReportCardReadDetail]
