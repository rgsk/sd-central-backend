from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_class_subject import (AcademicClassSubject,
                                           AcademicClassSubjectReadWithSubject)
from models.academic_session import AcademicSessionRead

if TYPE_CHECKING:
    from models.academic_session import AcademicSession
    from models.enrollment import Enrollment


class AcademicClassDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AcademicClassBase(SQLModel):
    academic_session_id: UUID = Field(
        foreign_key="academic_sessions.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    grade: str
    section: str


class AcademicClass(AcademicClassBase, AcademicClassDB, table=True):
    __tablename__ = "academic_classes"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "academic_session_id",
            "grade",
            "section",
            name="uq_academic_classes_session_grade_section",
        ),
    )
    academic_session: Optional["AcademicSession"] = Relationship(
        back_populates="academic_classes"
    )
    class_subjects: list["AcademicClassSubject"] = Relationship(
        back_populates="academic_class"
    )
    enrollments: list["Enrollment"] = Relationship(
        back_populates="academic_class"
    )
    pass


class AcademicClassCreate(AcademicClassBase):
    pass


class AcademicClassUpdate(SQLModel):
    academic_session_id: Optional[UUID] = None
    grade: Optional[str] = None
    section: Optional[str] = None


class AcademicClassId(SQLModel):
    id: UUID


class AcademicClassRead(AcademicClassBase, AcademicClassId):
    created_at: datetime
    academic_session: Optional["AcademicSessionRead"] = None


class AcademicClassReadWithSubjects(AcademicClassRead):
    class_subjects: list["AcademicClassSubjectReadWithSubject"] = []


class AcademicClassReadRaw(AcademicClassBase, AcademicClassId):
    created_at: datetime


class AcademicClassListResponse(SQLModel):
    total: int
    items: list[AcademicClassRead]
