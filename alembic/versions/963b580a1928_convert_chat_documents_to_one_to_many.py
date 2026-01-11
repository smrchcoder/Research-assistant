"""convert_chat_documents_to_one_to_many

Revision ID: 963b580a1928
Revises: 0da0346d327f
Create Date: 2026-01-09 18:18:58.591986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '963b580a1928'
down_revision: Union[str, Sequence[str], None] = '0da0346d327f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Convert many-to-many to one-to-many relationship."""
    
    # Step 1: Add chat_id column to documents table (nullable for now)
    op.add_column('documents', 
        sa.Column('chat_id', sa.Integer(), nullable=True)
    )
    
    # Step 2: Create foreign key constraint
    op.create_foreign_key(
        'fk_documents_chat_id_chats',
        'documents', 'chats',
        ['chat_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Step 3: Create index on chat_id for performance
    op.create_index(
        op.f('ix_documents_chat_id'),
        'documents',
        ['chat_id'],
        unique=False
    )
    
    # Step 4: Backfill chat_id from chat_documents association table
    # For each document, assign the first chat from the association table
    # (If multiple chats exist, only the first one will be kept)
    op.execute("""
        UPDATE documents
        SET chat_id = (
            SELECT chat_id
            FROM chat_documents
            WHERE chat_documents.document_id = documents.id
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1
            FROM chat_documents
            WHERE chat_documents.document_id = documents.id
        )
    """)
    
    # Step 5: Drop the chat_documents association table
    op.drop_table('chat_documents')
    
    # Optional: Make chat_id non-nullable if you want strict ownership
    # Uncomment the following lines if you want to enforce that every document must belong to a chat:
    # op.alter_column('documents', 'chat_id',
    #                 existing_type=sa.Integer(),
    #                 nullable=False)


def downgrade() -> None:
    """Downgrade schema: Convert one-to-many back to many-to-many relationship."""
    
    # Step 1: Recreate the chat_documents association table
    op.create_table(
        'chat_documents',
        sa.Column('chat_id', sa.Integer(), sa.ForeignKey('chats.id'), primary_key=True, nullable=False),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id'), primary_key=True, nullable=False),
    )
    
    # Step 2: Backfill chat_documents from documents.chat_id
    op.execute("""
        INSERT INTO chat_documents (chat_id, document_id)
        SELECT chat_id, id
        FROM documents
        WHERE chat_id IS NOT NULL
    """)
    
    # Step 3: Drop the foreign key constraint
    op.drop_constraint('fk_documents_chat_id_chats', 'documents', type_='foreignkey')
    
    # Step 4: Drop the index
    op.drop_index(op.f('ix_documents_chat_id'), table_name='documents')
    
    # Step 5: Drop the chat_id column
    op.drop_column('documents', 'chat_id')
