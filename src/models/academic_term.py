from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_session import AcademicSessionRead

if TYPE_CHECKING:
    from models.academic_session import AcademicSession
    from models.academic_class_subject import AcademicClassSubject
    from models.report_card import ReportCard


class AcademicTermType(str, Enum):
    ANNUAL = "annual"
    HALF_YEARLY = "half-yearly"
    QUARTERLY = "quarterly"


class AcademicTermDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class AcademicTermBase(SQLModel):
    academic_session_id: UUID = Field(
        foreign_key="academic_sessions.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    term_type: AcademicTermType


class AcademicTerm(AcademicTermBase, AcademicTermDB, table=True):
    __tablename__ = "academic_terms"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "academic_session_id",
            "term_type",
            name="uq_academic_terms_session_term_type",
        ),
    )
    academic_session: Optional["AcademicSession"] = Relationship(
        back_populates="academic_terms"
    )
    class_subjects: list["AcademicClassSubject"] = Relationship(
        back_populates="academic_term"
    )
    report_cards: list["ReportCard"] = Relationship(
        back_populates="academic_term"
    )
    pass


class AcademicTermCreate(AcademicTermBase):
    pass


class AcademicTermUpdate(SQLModel):
    academic_session_id: Optional[UUID] = None
    term_type: Optional[AcademicTermType] = None


class AcademicTermId(SQLModel):
    id: UUID


class AcademicTermRead(AcademicTermBase, AcademicTermId):
    created_at: datetime
    academic_session: Optional["AcademicSessionRead"] = None


class AcademicTermListResponse(SQLModel):
    total: int
    items: list[AcademicTermRead]
