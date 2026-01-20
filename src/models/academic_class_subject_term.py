from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.academic_class_subject import AcademicClassSubject
    from models.academic_term import AcademicTerm


class AcademicClassSubjectTermDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AcademicClassSubjectTermBase(SQLModel):
    academic_class_subject_id: UUID = Field(
        foreign_key="academic_class_subjects.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    academic_term_id: UUID = Field(
        foreign_key="academic_terms.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    highest_marks: Optional[int] = None
    average_marks: Optional[int] = None


class AcademicClassSubjectTerm(
    AcademicClassSubjectTermBase, AcademicClassSubjectTermDB, table=True
):
    __tablename__ = "academic_class_subject_terms"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "academic_class_subject_id",
            "academic_term_id",
            name="uq_class_subject_term",
        ),
    )
    academic_class_subject: Optional["AcademicClassSubject"] = Relationship(
        back_populates="class_subject_terms"
    )
    academic_term: Optional["AcademicTerm"] = Relationship(
        back_populates="class_subject_terms"
    )
    pass


class AcademicClassSubjectTermCreate(AcademicClassSubjectTermBase):
    pass


class AcademicClassSubjectTermUpdate(SQLModel):
    academic_class_subject_id: Optional[UUID] = None
    academic_term_id: Optional[UUID] = None
    highest_marks: Optional[int] = None
    average_marks: Optional[int] = None


class AcademicClassSubjectTermId(SQLModel):
    id: UUID


class AcademicClassSubjectTermRead(
    AcademicClassSubjectTermBase, AcademicClassSubjectTermId
):
    created_at: datetime


class AcademicClassSubjectTermListResponse(SQLModel):
    total: int
    items: list[AcademicClassSubjectTermRead]
