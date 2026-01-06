from datetime import datetime, timezone
from typing import TYPE_CHECKING, ClassVar, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_class import AcademicClassRead

if TYPE_CHECKING:
    from models.academic_class import AcademicClass
    from models.report_card import ReportCard
    from models.student import Student, StudentRead


class EnrollmentDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class EnrollmentBase(SQLModel):
    student_id: UUID = Field(
        foreign_key="students.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    academic_session_id: UUID = Field(
        foreign_key="academic_sessions.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    academic_class_id: UUID = Field(
        foreign_key="academic_classes.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    image: Optional[str] = None


class Enrollment(EnrollmentBase, EnrollmentDB, table=True):
    __tablename__: ClassVar[str] = "enrollments"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "academic_session_id",
            name="uq_enrollment_session",
        ),
    )
    student: Optional["Student"] = Relationship(
        back_populates="enrollments"
    )
    academic_class: Optional["AcademicClass"] = Relationship(
        back_populates="enrollments"
    )
    report_cards: list["ReportCard"] = Relationship(
        back_populates="enrollment"
    )


class EnrollmentCreate(EnrollmentBase):
    pass


class EnrollmentUpdate(SQLModel):
    student_id: Optional[UUID] = None
    academic_class_id: Optional[UUID] = None
    image: Optional[str] = None


class EnrollmentId(SQLModel):
    id: UUID


class EnrollmentRead(EnrollmentBase, EnrollmentId):
    created_at: datetime
    student: Optional["StudentRead"] = None
    academic_class: Optional[AcademicClassRead] = None


class EnrollmentReadRaw(EnrollmentBase, EnrollmentId):
    created_at: datetime


class EnrollmentListResponse(SQLModel):
    total: int
    items: list[EnrollmentRead]


try:
    from models.student import StudentRead

    EnrollmentRead.model_rebuild(
        _types_namespace={"StudentRead": StudentRead}
    )
except ImportError:
    pass
