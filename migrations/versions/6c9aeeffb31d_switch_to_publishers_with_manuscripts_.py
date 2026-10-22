"""Switch to publishers with manuscripts, chapters and notes

Revision ID: 6c9aeeffb31d
Revises: 80e70d5fe567
Create Date: 2026-10-20 14:33:14.864382

What this migration does:
- Removes the old submission workflow tables (submissions, messages,
  meetings, editor_notes) and the presses table. Any old submissions
  are deleted.
- Every user becomes a publisher: the old role and press_id columns are
  removed and a press_name column is added. Existing editors keep their
  press's name; anyone without a press gets "My press".
- Adds the new manuscripts, chapters and notes tables.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c9aeeffb31d'
down_revision = '80e70d5fe567'
branch_labels = None
depends_on = None


def upgrade():
    """Move the database to the publisher/manuscript structure."""
    # 1. Remove the old submission workflow tables (children first).
    op.drop_table('messages')
    op.drop_table('meetings')
    op.drop_table('editor_notes')
    op.drop_table('submissions')

    # 2. Give every user a press name, copied from their old press.
    op.add_column(
        'users', sa.Column('press_name', sa.String(length=120), nullable=True)
    )
    op.execute(
        "UPDATE users SET press_name = "
        "(SELECT presses.name FROM presses WHERE presses.id = users.press_id)"
    )
    op.execute(
        "UPDATE users SET press_name = 'My press' WHERE press_name IS NULL"
    )

    # 3. Remove the old role/press columns. Batch mode rebuilds the table,
    #    which SQLite needs in order to drop columns.
    with op.batch_alter_table('users', recreate='always') as batch_op:
        batch_op.alter_column(
            'press_name', existing_type=sa.String(length=120), nullable=False
        )
        batch_op.drop_column('press_id')
        batch_op.drop_column('role')

    op.drop_table('presses')

    # 4. Add the new tables.
    op.create_table(
        'manuscripts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('author_name', sa.String(length=120), nullable=False),
        sa.Column('genre', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('manuscript_id', sa.Integer(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['manuscript_id'], ['manuscripts.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    """Go back to the old structure (tables only; data is not restored)."""
    op.drop_table('notes')
    op.drop_table('chapters')
    op.drop_table('manuscripts')

    op.create_table(
        'presses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('website', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('open_for_submissions', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    with op.batch_alter_table('users', recreate='always') as batch_op:
        batch_op.add_column(sa.Column(
            'role', sa.String(length=50), nullable=False,
            server_default='editor',
        ))
        batch_op.add_column(
            sa.Column('press_id', sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_users_press_id', 'presses', ['press_id'], ['id']
        )
        batch_op.drop_column('press_name')

    op.create_table(
        'submissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('genre', sa.String(length=80), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('synopsis', sa.Text(), nullable=False),
        sa.Column('manuscript_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('writer_id', sa.Integer(), nullable=False),
        sa.Column('press_id', sa.Integer(), nullable=False),
        sa.Column('assigned_editor_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_editor_id'], ['users.id']),
        sa.ForeignKeyConstraint(['press_id'], ['presses.id']),
        sa.ForeignKeyConstraint(['writer_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'editor_notes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id']),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'meetings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('submission_id', sa.Integer(), nullable=False),
        sa.Column('sender_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['sender_id'], ['users.id']),
        sa.ForeignKeyConstraint(['submission_id'], ['submissions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
