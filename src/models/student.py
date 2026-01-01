from datetime import date
from typing import ClassVar, Optional

from sqlmodel import Field, SQLModel


class StudentDB(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)


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
    id: int


class StudentRead(StudentBase, StudentId):
    pass
