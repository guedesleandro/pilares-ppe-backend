"""change_dosage_mg_to_decimal

Revision ID: 96d83a58877c
Revises: 2dee76f725c4
Create Date: 2025-11-24 20:42:30.826162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '96d83a58877c'
down_revision: Union[str, None] = '2dee76f725c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alterar coluna dosage_mg de Integer para Numeric(10, 2)
    op.alter_column('sessions', 'dosage_mg',
                    type_=sa.Numeric(precision=10, scale=2),
                    existing_type=sa.Integer(),
                    existing_nullable=True)


def downgrade() -> None:
    # Reverter para Integer (perdendo casas decimais)
    op.alter_column('sessions', 'dosage_mg',
                    type_=sa.Integer(),
                    existing_type=sa.Numeric(precision=10, scale=2),
                    existing_nullable=True)
