"""Add user_id tenant isolation columns to leads, projects, and agent_runs

Revision ID: 002_user_id_isolation
Revises: 001_initial
Create Date: 2026-08-14
"""
from alembic import op
import sqlalchemy as sa

revision = '002_user_id_isolation'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Safe migration: Add nullable user_id column with foreign key to users.id
    op.add_column('leads', sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True))
    op.create_index('ix_leads_user_id', 'leads', ['user_id'])

    op.add_column('projects', sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True))
    op.create_index('ix_projects_user_id', 'projects', ['user_id'])

    op.add_column('agent_runs', sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True))
    op.create_index('ix_agent_runs_user_id', 'agent_runs', ['user_id'])


def downgrade():
    op.drop_index('ix_agent_runs_user_id', table_name='agent_runs')
    op.drop_column('agent_runs', 'user_id')

    op.drop_index('ix_projects_user_id', table_name='projects')
    op.drop_column('projects', 'user_id')

    op.drop_index('ix_leads_user_id', table_name='leads')
    op.drop_column('leads', 'user_id')
