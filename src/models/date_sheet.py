from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_class import AcademicClassRead
from models.academic_term import AcademicTermRead
from models.date_sheet_subject import DateSheetSubjectRead

if TYPE_CHECKING:
    from models.academic_class import AcademicClass
    from models.academic_term import AcademicTerm
    from models.date_sheet_subject import DateSheetSubject


class DateSheetDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class DateSheetBase(SQLModel):
    academic_class_id: UUID = Field(
        foreign_key="academic_classes.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    academic_term_id: UUID = Field(
        foreign_key="academic_terms.id",
        sa_type=PG_UUID(as_uuid=True),
    )


class DateSheet(DateSheetBase, DateSheetDB, table=True):
    __tablename__ = "date_sheets"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "academic_class_id",
            "academic_term_id",
            name="uq_date_sheets_class_term",
        ),
    )
    academic_class: Optional["AcademicClass"] = Relationship(
        back_populates="date_sheets"
    )
    academic_term: Optional["AcademicTerm"] = Relationship(
        back_populates="date_sheets"
    )
    date_sheet_subjects: list["DateSheetSubject"] = Relationship(
        back_populates="date_sheet",
        sa_relationship_kwargs={"passive_deletes": True},
    )
    pass


class DateSheetCreate(DateSheetBase):
    pass


class DateSheetUpdate(SQLModel):
    academic_class_id: Optional[UUID] = None
    academic_term_id: Optional[UUID] = None


class DateSheetId(SQLModel):
    id: UUID


class DateSheetRead(DateSheetBase, DateSheetId):
    created_at: datetime
    academic_class: Optional["AcademicClassRead"] = None
    academic_term: Optional["AcademicTermRead"] = None


class DateSheetReadDetail(DateSheetRead):
    date_sheet_subjects: list[DateSheetSubjectRead] = []


class DateSheetReadRaw(DateSheetBase, DateSheetId):
    created_at: datetime


class DateSheetListResponse(SQLModel):
    total: int
    items: list[DateSheetRead]
