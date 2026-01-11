"""add chat_documents relation and document path

Revision ID: 0da0346d327f
Revises: bbfd9ea70e5b
Create Date: 2026-01-06 22:52:33.126981

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0da0346d327f'
down_revision: Union[str, Sequence[str], None] = 'bbfd9ea70e5b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create chats table
    op.create_table(
        'chats',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('chat_name', sa.String(), nullable=False),
        sa.Column('chat_history', postgresql.JSON(), nullable=False),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_chats_id'), 'chats', ['id'], unique=False)
    op.create_index(op.f('ix_chats_chat_name'), 'chats', ['chat_name'], unique=True)

    # Create association table chat_documents
    op.create_table(
        'chat_documents',
        sa.Column('chat_id', sa.Integer(), sa.ForeignKey('chats.id'), primary_key=True, nullable=False),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id'), primary_key=True, nullable=False),
    )

    # Add optional path column to documents to store PDF path
    op.add_column('documents', sa.Column('path', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove path column from documents
    op.drop_column('documents', 'path')

    # Drop association table
    op.drop_table('chat_documents')

    # Drop chats table
    op.drop_index(op.f('ix_chats_chat_name'), table_name='chats')
    op.drop_index(op.f('ix_chats_id'), table_name='chats')
    op.drop_table('chats')
