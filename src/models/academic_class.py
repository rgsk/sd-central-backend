from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_session import AcademicSessionRead

if TYPE_CHECKING:
    from models.academic_session import AcademicSession
    from models.student import Student


class AcademicClassDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )


class AcademicClassBase(SQLModel):
    academic_session_id: UUID = Field(
        foreign_key="academic_sessions.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    grade: str
    section: str


class AcademicClass(AcademicClassBase, AcademicClassDB, table=True):
    __tablename__ = "academic_classes"  # type: ignore
    academic_session: Optional["AcademicSession"] = Relationship(
        back_populates="academic_classes"
    )
    students: list["Student"] = Relationship(back_populates="academic_class")
    pass


class AcademicClassCreate(AcademicClassBase):
    pass


class AcademicClassUpdate(SQLModel):
    academic_session_id: Optional[UUID] = None
    grade: Optional[str] = None
    section: Optional[str] = None


class AcademicClassId(SQLModel):
    id: UUID


class AcademicClassRead(AcademicClassBase, AcademicClassId):
    academic_session: Optional["AcademicSessionRead"] = None


class AcademicClassReadRaw(AcademicClassBase, AcademicClassId):
    pass
