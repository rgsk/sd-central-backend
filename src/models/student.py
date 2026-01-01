from datetime import date
from typing import ClassVar, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class StudentDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )


class StudentBase(SQLModel):
    registration_no: str
    name: str
    class_value: str
    section: str
    dob: date
    father_name: str
    mother_name: str
    image: Optional[str] = None


class Student(StudentBase, StudentDB, table=True):
    __tablename__: ClassVar[str] = "students"  # type: ignore[reportIncompatibleVariableOverride]


class StudentCreate(StudentBase):
    pass


class StudentUpdate(SQLModel):
    registration_no: Optional[str] = None
    name: Optional[str] = None
    class_value: Optional[str] = None
    section: Optional[str] = None
    dob: Optional[date] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    image: Optional[str] = None


class StudentId(SQLModel):
    id: UUID


class StudentRead(StudentBase, StudentId):
    pass
