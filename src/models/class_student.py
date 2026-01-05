from datetime import datetime, timezone
from typing import TYPE_CHECKING, ClassVar, Optional
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, Relationship, SQLModel

from models.academic_class import AcademicClassRead

if TYPE_CHECKING:
    from models.academic_class import AcademicClass
    from models.report_card import ReportCard
    from models.student import Student, StudentRead


class ClassStudentDB(SQLModel):
    id: Optional[UUID] = Field(
        default_factory=uuid4,
        primary_key=True,
        sa_type=PG_UUID(as_uuid=True),
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ClassStudentBase(SQLModel):
    student_id: UUID = Field(
        foreign_key="students.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    academic_class_id: UUID = Field(
        foreign_key="academic_classes.id",
        sa_type=PG_UUID(as_uuid=True),
    )
    image: Optional[str] = None


class ClassStudent(ClassStudentBase, ClassStudentDB, table=True):
    __tablename__: ClassVar[str] = "class_students"  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "academic_class_id",
            name="uq_class_student_class",
        ),
    )
    student: Optional["Student"] = Relationship(
        back_populates="class_students"
    )
    academic_class: Optional["AcademicClass"] = Relationship(
        back_populates="class_students"
    )
    report_cards: list["ReportCard"] = Relationship(
        back_populates="class_student"
    )


class ClassStudentCreate(ClassStudentBase):
    pass


class ClassStudentUpdate(SQLModel):
    student_id: Optional[UUID] = None
    academic_class_id: Optional[UUID] = None
    image: Optional[str] = None


class ClassStudentId(SQLModel):
    id: UUID


class ClassStudentRead(ClassStudentBase, ClassStudentId):
    created_at: datetime
    student: Optional["StudentRead"] = None
    academic_class: Optional[AcademicClassRead] = None


class ClassStudentReadRaw(ClassStudentBase, ClassStudentId):
    created_at: datetime


class ClassStudentListResponse(SQLModel):
    total: int
    items: list[ClassStudentRead]


try:
    from models.student import StudentRead

    ClassStudentRead.model_rebuild(
        _types_namespace={"StudentRead": StudentRead}
    )
except ImportError:
    pass
