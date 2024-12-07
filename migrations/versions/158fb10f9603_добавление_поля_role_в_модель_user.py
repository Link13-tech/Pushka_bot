"""Добавление поля role в модель User

Revision ID: 158fb10f9603
Revises: 32ad117cd0df
Create Date: 2024-12-07 17:43:14.345375

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '158fb10f9603'
down_revision: Union[str, None] = '32ad117cd0df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём ENUM тип в базе данных
    user_role_enum = postgresql.ENUM('USER', 'ADMIN', name='userrole')
    user_role_enum.create(op.get_bind())

    # Добавляем столбец role
    op.add_column('users', sa.Column('role', sa.Enum('USER', 'ADMIN', name='userrole'), nullable=False, server_default='USER'))


def downgrade() -> None:
    # Удаляем столбец role
    op.drop_column('users', 'role')

    # Удаляем ENUM тип из базы данных
    user_role_enum = postgresql.ENUM('USER', 'ADMIN', name='userrole')
    user_role_enum.drop(op.get_bind())
