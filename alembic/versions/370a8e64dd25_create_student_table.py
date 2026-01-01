"""create student table

Revision ID: 370a8e64dd25
Revises: 
Create Date: 2026-01-01 11:50:43.702614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '370a8e64dd25'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "student",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
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
        "ix_student_registration_no", "student", ["registration_no"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_student_registration_no", table_name="student")
    op.drop_table("student")
