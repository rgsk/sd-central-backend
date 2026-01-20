from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.subject import SubjectRead

if TYPE_CHECKING:
    from models.academic_class import AcademicClass
    from models.academic_class_subject_term import AcademicClassSubjectTerm
    from models.date_sheet_subject import DateSheetSubject
    from models.report_card_subject import ReportCardSubject
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
    is_additional: bool = False
    position: int = Field(ge=1)


class AcademicClassSubject(
    AcademicClassSubjectBase, AcademicClassSubjectDB, table=True
):
    __tablename__ = "academic_class_subjects"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "academic_class_id",
            "subject_id",
            name="uq_class_subject",
        ),
        UniqueConstraint(
            "academic_class_id",
            "is_additional",
            "position",
            name="uq_class_subject_group_position",
        ),
    )
    academic_class: Optional["AcademicClass"] = Relationship(
        back_populates="class_subjects"
    )
    subject: Optional["Subject"] = Relationship(
        back_populates="class_subjects"
    )
    report_card_subjects: list["ReportCardSubject"] = Relationship(
        back_populates="academic_class_subject",
        sa_relationship_kwargs={"passive_deletes": True},
    )
    date_sheet_subjects: list["DateSheetSubject"] = Relationship(
        back_populates="academic_class_subject",
        sa_relationship_kwargs={"passive_deletes": True},
    )
    class_subject_terms: list["AcademicClassSubjectTerm"] = Relationship(
        back_populates="academic_class_subject",
        sa_relationship_kwargs={"passive_deletes": True},
    )
    pass


class AcademicClassSubjectCreate(AcademicClassSubjectBase):
    pass


class AcademicClassSubjectUpdate(SQLModel):
    academic_class_id: Optional[UUID] = None
    subject_id: Optional[UUID] = None
    is_additional: Optional[bool] = None
    position: Optional[int] = None


class AcademicClassSubjectId(SQLModel):
    id: UUID


class AcademicClassSubjectRead(
    AcademicClassSubjectBase, AcademicClassSubjectId
):
    created_at: datetime


class AcademicClassSubjectReadWithSubject(AcademicClassSubjectRead):
    subject: Optional["SubjectRead"] = None


class AcademicClassSubjectReorderItem(SQLModel):
    id: UUID
    position: int = Field(ge=1)


class AcademicClassSubjectReorderRequest(SQLModel):
    items: list[AcademicClassSubjectReorderItem]


class AcademicClassSubjectListResponse(SQLModel):
    total: int
    items: list[AcademicClassSubjectReadWithSubject]
