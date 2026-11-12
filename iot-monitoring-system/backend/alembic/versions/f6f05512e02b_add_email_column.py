"""add email column

Revision ID: f6f05512e02b
Revises: f5cefbc06be4
Create Date: 2025-03-12 17:37:51.032477
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6f05512e02b'
down_revision: Union[str, None] = 'f5cefbc06be4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем новый столбец email в таблицу users
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))

    # Убираем команды удаления таблиц
    # op.drop_table('devices')  # Удаляем эту строку
    # op.drop_table('profiles')  # Удаляем эту строку
    # op.drop_table('sensor_data')  # Удаляем эту строку
    # op.drop_table('users')  # Удаляем эту строку


def downgrade() -> None:
    # Убираем столбец email в случае отката миграции
    op.drop_column('users', 'email')

    # Восстанавливаем таблицы, если потребуется (оставляем их в случае отката)
    op.create_table('users',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('users_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('username', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('hashed_password', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('is_active', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='users_pkey'),
    sa.UniqueConstraint('username', name='users_username_key'),
    postgresql_ignore_search_path=False
    )
    op.create_table('sensor_data',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('device_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('temperature', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False),
    sa.Column('humidity', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('timestamp', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['device_id'], ['devices.id'], name='sensor_data_device_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='sensor_data_pkey')
    )
    op.create_table('profiles',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='profiles_user_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='profiles_pkey')
    )
    op.create_table('devices',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('status', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('owner_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name='devices_owner_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='devices_pkey')
    )
    # ### end Alembic commands ### 
