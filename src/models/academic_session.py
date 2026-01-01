from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.academic_class import AcademicClass


class AcademicSessionDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )


class AcademicSessionBase(SQLModel):
    year: str


class AcademicSession(AcademicSessionBase, AcademicSessionDB, table=True):
    __tablename__ = "academic_sessions"  # type: ignore
    academic_classes: list["AcademicClass"] = Relationship(
        back_populates="academic_session"
    )
    pass


class AcademicSessionCreate(AcademicSessionBase):
    pass


class AcademicSessionUpdate(SQLModel):
    year: Optional[str] = None


class AcademicSessionId(SQLModel):
    id: UUID


class AcademicSessionRead(AcademicSessionBase, AcademicSessionId):
    pass
