"""Initialize the Alembic migration history.

Revision ID: 20260823_01
Revises:
Create Date: 2026-08-23 00:00:00.000000
"""

from collections.abc import Sequence

revision: str = "20260823_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Establish version tracking before domain tables are introduced in M1-T10."""


def downgrade() -> None:
    """Remove no schema objects; this migration only establishes version tracking."""
