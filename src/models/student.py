from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, ClassVar, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.class_student import ClassStudentRead

if TYPE_CHECKING:
    from models.class_student import ClassStudent


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
    dob: date
    father_name: str
    mother_name: str


class Student(StudentBase, StudentDB, table=True):
    __tablename__: ClassVar[str] = "students"  # type: ignore
    class_students: list["ClassStudent"] = Relationship(
        back_populates="student"
    )


class StudentCreate(StudentBase):
    pass


class StudentUpdate(SQLModel):
    registration_no: Optional[str] = None
    name: Optional[str] = None
    dob: Optional[date] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None


class StudentId(SQLModel):
    id: UUID


class StudentRead(StudentBase, StudentId):
    created_at: datetime
    class_student: Optional["ClassStudentRead"] = None


class StudentReadRaw(StudentBase, StudentId):
    created_at: datetime


class StudentListResponse(SQLModel):
    total: int
    items: list[StudentRead]
