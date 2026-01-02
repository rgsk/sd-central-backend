from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, ClassVar, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_class import AcademicClassRead

if TYPE_CHECKING:
    from models.academic_class import AcademicClass
    from models.report_card import ReportCard


class StudentDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class StudentBase(SQLModel):
    registration_no: str = Field(index=True, unique=True)
    name: str
    academic_class_id: Optional[UUID] = Field(
        default=None,
        foreign_key="academic_classes.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    dob: date
    father_name: str
    mother_name: str
    image: Optional[str] = None


class Student(StudentBase, StudentDB, table=True):
    __tablename__: ClassVar[str] = "students"  # type: ignore
    academic_class: Optional["AcademicClass"] = Relationship(
        back_populates="students")
    report_cards: list["ReportCard"] = Relationship(
        back_populates="student"
    )


class StudentCreate(StudentBase):
    pass


class StudentUpdate(SQLModel):
    registration_no: Optional[str] = None
    name: Optional[str] = None
    academic_class_id: Optional[UUID] = None
    dob: Optional[date] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    image: Optional[str] = None


class StudentId(SQLModel):
    id: UUID


class StudentRead(StudentBase, StudentId):
    created_at: datetime
    academic_class: Optional["AcademicClassRead"] = None


class StudentReadRaw(StudentBase, StudentId):
    created_at: datetime


class StudentListResponse(SQLModel):
    total: int
    items: list[StudentRead]
