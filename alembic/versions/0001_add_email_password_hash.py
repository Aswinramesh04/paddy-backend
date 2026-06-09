"""add email and password_hash to users

Revision ID: 0001_add_email_password_hash
Revises: 
Create Date: 2026-06-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_email_password_hash'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email', sa.String(length=254), nullable=True))
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.add_column('users', sa.Column('password_hash', sa.String(length=256), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_column('users', 'email')
