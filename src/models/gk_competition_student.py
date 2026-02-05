from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class GKCompetitionStudentDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class GKCompetitionStudentBase(SQLModel):
    name: str
    roll_no: str
    father_name: str
    mother_name: str
    class_name: str
    school_name: str
    school_address: str
    aadhaar_no: str
    group: str
    paper_medium: str
    exam_center: str
    contact_no: str
    marks: Optional[int] = None


class GKCompetitionStudent(
    GKCompetitionStudentBase, GKCompetitionStudentDB, table=True
):
    __tablename__ = "gk_competition_students"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "aadhaar_no",
            name="uq_gk_competition_students_aadhaar_no",
        ),
        UniqueConstraint(
            "roll_no",
            name="uq_gk_competition_students_roll_no",
        ),
    )
    pass


class GKCompetitionStudentCreate(GKCompetitionStudentBase):
    pass


class GKCompetitionStudentUpdate(SQLModel):
    name: Optional[str] = None
    roll_no: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    class_name: Optional[str] = None
    school_name: Optional[str] = None
    school_address: Optional[str] = None
    aadhaar_no: Optional[str] = None
    group: Optional[str] = None
    paper_medium: Optional[str] = None
    exam_center: Optional[str] = None
    contact_no: Optional[str] = None
    marks: Optional[int] = None


class GKCompetitionStudentId(SQLModel):
    id: UUID


class GKCompetitionStudentRead(
    GKCompetitionStudentBase, GKCompetitionStudentId
):
    created_at: datetime


class GKCompetitionStudentReadRaw(
    GKCompetitionStudentBase, GKCompetitionStudentId
):
    created_at: datetime


class GKCompetitionStudentListResponse(SQLModel):
    total: int
    items: list[GKCompetitionStudentRead]
