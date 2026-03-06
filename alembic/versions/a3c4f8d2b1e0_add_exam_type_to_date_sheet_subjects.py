"""add_exam_type_to_date_sheet_subjects

Revision ID: a3c4f8d2b1e0
Revises: 6a89ea830441
Create Date: 2026-03-06 11:05:00.000000

"""
import os
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3c4f8d2b1e0"
down_revision: Union[str, Sequence[str], None] = "6a89ea830441"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SCHEMA = os.getenv("DB_NAMESPACE") or None


def upgrade() -> None:
    """Upgrade schema."""
    exam_type_enum = sa.Enum(
        "WRITTEN",
        "ORAL",
        name="datesheetsubjectexamtype",
        schema=_SCHEMA,
    )
    exam_type_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "date_sheet_subjects",
        sa.Column(
            "exam_type",
            exam_type_enum,
            nullable=False,
            server_default=sa.text("'WRITTEN'"),
        ),
        schema=_SCHEMA,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("date_sheet_subjects", "exam_type", schema=_SCHEMA)
    exam_type_enum = sa.Enum(
        "WRITTEN",
        "ORAL",
        name="datesheetsubjectexamtype",
        schema=_SCHEMA,
    )
    exam_type_enum.drop(op.get_bind(), checkfirst=True)
