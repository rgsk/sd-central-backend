from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_class import AcademicClassReadRaw
from models.academic_session import AcademicSessionRead
from models.academic_term import AcademicTermReadRaw

if TYPE_CHECKING:
    from models.academic_class import AcademicClass
    from models.academic_session import AcademicSession
    from models.academic_term import AcademicTerm


class UserRole(str, Enum):
    ADMIN = "admin"
    TEACHER = "teacher"


class UserDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UserBase(SQLModel):
    email: str = Field(index=True, unique=True)
    role: UserRole
    default_academic_session_id: Optional[UUID] = Field(
        default=None,
        foreign_key="academic_sessions.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    default_academic_term_id: Optional[UUID] = Field(
        default=None,
        foreign_key="academic_terms.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    default_academic_class_id: Optional[UUID] = Field(
        default=None,
        foreign_key="academic_classes.id",
        sa_type=PG_UUID(as_uuid=True),
    )


class User(UserBase, UserDB, table=True):
    __tablename__ = "users"  # type: ignore
    default_academic_session: Optional["AcademicSession"] = Relationship()
    default_academic_term: Optional["AcademicTerm"] = Relationship()
    default_academic_class: Optional["AcademicClass"] = Relationship()


class UserCreate(UserBase):
    pass


class UserUpdate(SQLModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
    default_academic_session_id: Optional[UUID] = None
    default_academic_term_id: Optional[UUID] = None
    default_academic_class_id: Optional[UUID] = None


class UserId(SQLModel):
    id: UUID


class UserRead(UserBase, UserId):
    created_at: datetime
    default_academic_session: Optional[AcademicSessionRead] = None
    default_academic_term: Optional[AcademicTermReadRaw] = None
    default_academic_class: Optional[AcademicClassReadRaw] = None


class UserReadRaw(UserBase, UserId):
    created_at: datetime


class UserListResponse(SQLModel):
    total: int
    items: list[UserRead]
