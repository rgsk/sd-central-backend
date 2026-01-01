"""create students table

Revision ID: 370a8e64dd25
Revises: 
Create Date: 2026-01-01 11:50:43.702614

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '370a8e64dd25'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "students",
        sa.Column("id", PG_UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("registration_no", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("class_value", sa.String(), nullable=False),
        sa.Column("section", sa.String(), nullable=False),
        sa.Column("dob", sa.Date(), nullable=False),
        sa.Column("father_name", sa.String(), nullable=False),
        sa.Column("mother_name", sa.String(), nullable=False),
        sa.Column("image", sa.String(), nullable=True),
        sa.UniqueConstraint("registration_no"),
    )
    op.create_index(
        "ix_students_registration_no", "students", ["registration_no"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_students_registration_no", table_name="students")
    op.drop_table("students")
