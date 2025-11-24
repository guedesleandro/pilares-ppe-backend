"""rename_muscle_mass_kg_to_percentage

Revision ID: 2dee76f725c4
Revises: f47e7f5820fa
Create Date: 2025-11-24 20:29:55.788039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2dee76f725c4'
down_revision: Union[str, None] = 'f47e7f5820fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Renomear coluna e alterar tipo para porcentagem
    op.alter_column(
        'body_compositions',
        'muscle_mass_kg',
        new_column_name='muscle_mass_percentage',
        type_=sa.Numeric(precision=5, scale=2),
        existing_type=sa.Numeric(precision=7, scale=2),
        existing_nullable=False
    )


def downgrade() -> None:
    # Reverter para o nome e tipo original
    op.alter_column(
        'body_compositions',
        'muscle_mass_percentage',
        new_column_name='muscle_mass_kg',
        type_=sa.Numeric(precision=7, scale=2),
        existing_type=sa.Numeric(precision=5, scale=2),
        existing_nullable=False
    )
