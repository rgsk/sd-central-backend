from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.student import Student


class AcademicClassDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )


class AcademicClassBase(SQLModel):
    session: str
    grade: str
    section: str


class AcademicClass(AcademicClassBase, AcademicClassDB, table=True):
    __tablename__ = "academic_classes"  # type: ignore
    students: list["Student"] = Relationship(back_populates="academic_class")
    pass


class AcademicClassCreate(AcademicClassBase):
    pass


class AcademicClassUpdate(SQLModel):
    session: Optional[str] = None
    grade: Optional[str] = None
    section: Optional[str] = None


class AcademicClassId(SQLModel):
    id: UUID


class AcademicClassRead(AcademicClassBase, AcademicClassId):
    pass
