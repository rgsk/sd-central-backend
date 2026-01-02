from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.subject import SubjectRead

if TYPE_CHECKING:
    from models.academic_class import AcademicClass
    from models.academic_term import AcademicTerm
    from models.subject import Subject


class AcademicClassSubjectDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AcademicClassSubjectBase(SQLModel):
    academic_class_id: UUID = Field(
        foreign_key="academic_classes.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    subject_id: UUID = Field(
        foreign_key="subjects.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    academic_term_id: UUID = Field(
        foreign_key="academic_terms.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    highest_marks: Optional[int] = None
    average_marks: Optional[int] = None
    is_additional: bool = False


class AcademicClassSubject(
    AcademicClassSubjectBase, AcademicClassSubjectDB, table=True
):
    __tablename__ = "academic_class_subjects"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "academic_class_id",
            "subject_id",
            "academic_term_id",
            name="uq_class_subject_term",
        ),
    )
    academic_class: Optional["AcademicClass"] = Relationship(
        back_populates="class_subjects"
    )
    subject: Optional["Subject"] = Relationship(
        back_populates="class_subjects"
    )
    academic_term: Optional["AcademicTerm"] = Relationship(
        back_populates="class_subjects"
    )
    pass


class AcademicClassSubjectCreate(AcademicClassSubjectBase):
    pass


class AcademicClassSubjectUpdate(SQLModel):
    academic_class_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    academic_term_id: Optional[UUID] = None
    highest_marks: Optional[int] = None
    average_marks: Optional[int] = None
    is_additional: Optional[bool] = None


class AcademicClassSubjectId(SQLModel):
    id: UUID


class AcademicClassSubjectRead(
    AcademicClassSubjectBase, AcademicClassSubjectId
):
    created_at: datetime


class AcademicClassSubjectReadWithSubject(AcademicClassSubjectRead):
    subject: Optional["SubjectRead"] = None


class AcademicClassSubjectListResponse(SQLModel):
    total: int
    items: list[AcademicClassSubjectRead]
