from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from models.academic_class import AcademicClass
    from models.academic_term import AcademicTerm


class AcademicSessionDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AcademicSessionBase(SQLModel):
    year: str


class AcademicSession(AcademicSessionBase, AcademicSessionDB, table=True):
    __tablename__ = "academic_sessions"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "year",
            name="academic_sessions_year_key",
        ),
    )
    academic_classes: list["AcademicClass"] = Relationship(
        back_populates="academic_session"
    )
    academic_terms: list["AcademicTerm"] = Relationship(
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
    created_at: datetime


class AcademicSessionListResponse(SQLModel):
    total: int
    items: list[AcademicSessionRead]
