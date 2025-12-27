from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import date


class StudentDB(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)


class StudentBase(SQLModel):
    registration_no: str = Field(index=True, unique=True)
    name: str
    class_value: str
    section: str
    dob: date
    father_name: str
    mother_name: str
    image: Optional[str] = None


class Student(StudentBase, StudentDB, table=True):
    pass


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
