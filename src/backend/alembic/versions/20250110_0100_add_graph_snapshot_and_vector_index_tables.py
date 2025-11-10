"""Add graph_snapshot and vector_index tables for v2

Revision ID: 001_graph_rag_v2
Revises:
Create Date: 2025-01-10 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_graph_rag_v2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # GraphSnapshot 테이블 생성
    op.create_table(
        'graph_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('commit_hash', sa.String(length=40), nullable=False, unique=True, index=True),
        sa.Column('repo_url', sa.String(), nullable=False),
        sa.Column('branch', sa.String(), server_default='main'),
        sa.Column('node_count', sa.Integer(), server_default='0'),
        sa.Column('edge_count', sa.Integer(), server_default='0'),
        sa.Column('node_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('neo4j_database', sa.String(), server_default='neo4j'),
        sa.Column('neo4j_snapshot_id', sa.String(), nullable=True),
        sa.Column('is_valid', sa.Boolean(), server_default='true'),
        sa.Column('build_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )

    # VectorIndex 테이블 생성
    op.create_table(
        'vector_indices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('index_name', sa.String(), nullable=False, index=True),
        sa.Column('commit_hash', sa.String(length=40), nullable=False, index=True),
        sa.Column('chunk_count', sa.Integer(), server_default='0'),
        sa.Column('embedding_dimension', sa.Integer(), server_default='1536'),
        sa.Column('embedding_model', sa.String(), nullable=False),
        sa.Column('opensearch_endpoint', sa.String(), nullable=True),
        sa.Column('index_settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_valid', sa.Boolean(), server_default='true'),
        sa.Column('indexing_duration_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('vector_indices')
    op.drop_table('graph_snapshots')
