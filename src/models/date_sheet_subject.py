from datetime import date, datetime, time, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_class_subject import AcademicClassSubjectReadWithSubject

if TYPE_CHECKING:
    from models.academic_class_subject import AcademicClassSubject
    from models.date_sheet import DateSheet


class DateSheetSubjectDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class DateSheetSubjectBase(SQLModel):
    date_sheet_id: UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey(
                "date_sheets.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )
    academic_class_subject_id: UUID = Field(
        sa_column=Column(
            PG_UUID(as_uuid=True),
            ForeignKey(
                "academic_class_subjects.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        )
    )
    paper_code: Optional[str] = None
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class DateSheetSubject(
    DateSheetSubjectBase, DateSheetSubjectDB, table=True
):
    __tablename__ = "date_sheet_subjects"  # type: ignore
    date_sheet: Optional["DateSheet"] = Relationship(
        back_populates="date_sheet_subjects"
    )
    academic_class_subject: Optional["AcademicClassSubject"] = Relationship(
        back_populates="date_sheet_subjects"
    )
    pass


class DateSheetSubjectCreate(DateSheetSubjectBase):
    pass


class DateSheetSubjectUpdate(SQLModel):
    date_sheet_id: Optional[UUID] = None
    academic_class_subject_id: Optional[UUID] = None
    paper_code: Optional[str] = None
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class DateSheetSubjectId(SQLModel):
    id: UUID


class DateSheetSubjectRead(
    DateSheetSubjectBase, DateSheetSubjectId
):
    created_at: datetime
    academic_class_subject: Optional[
        AcademicClassSubjectReadWithSubject
    ] = None


class DateSheetSubjectReadRaw(
    DateSheetSubjectBase, DateSheetSubjectId
):
    created_at: datetime


class DateSheetSubjectListResponse(SQLModel):
    total: int
    items: list[DateSheetSubjectRead]
