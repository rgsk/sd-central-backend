from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.academic_class_subject import AcademicClassSubject
    from models.report_card_subject import ReportCardSubject


class SubjectDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class SubjectBase(SQLModel):
    name: str = Field(index=True, unique=True)


class Subject(SubjectBase, SubjectDB, table=True):
    __tablename__ = "subjects"  # type: ignore
    class_subjects: list["AcademicClassSubject"] = Relationship(
        back_populates="subject"
    )
    report_card_subjects: list["ReportCardSubject"] = Relationship(
        back_populates="subject"
    )
    pass


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(SQLModel):
    name: Optional[str] = None


class SubjectId(SQLModel):
    id: UUID


class SubjectRead(SubjectBase, SubjectId):
    created_at: datetime


class SubjectListResponse(SQLModel):
    total: int
    items: list[SubjectRead]
