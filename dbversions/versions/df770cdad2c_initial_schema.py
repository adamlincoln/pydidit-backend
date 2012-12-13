"""Initial schema

Revision ID: df770cdad2c
Revises: None
Create Date: 2012-12-04 15:57:17.507991

"""

# revision identifiers, used by Alembic.
revision = 'df770cdad2c'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'todos',
        sa.Column('id', sa.Integer(), nullable = False, primary_key = True),
        sa.Column('description', sa.Unicode(length = 255), nullable = False),
        sa.Column('state', sa.Enum(
            'active',
            'completed',
        ), nullable = False),
        sa.Column('due', sa.DateTime(), nullable = True),
        sa.Column('created_at', sa.DateTime(), nullable = False),
        sa.Column('completed_at', sa.DateTime(), nullable = True),
        sa.Column('modified_at', sa.DateTime(), nullable = False),
        sa.Column('show_from', sa.DateTime(), nullable = True),
        sa.Column('display_position', sa.Unicode(length = 50), nullable = False),
    )

    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable = False, primary_key = True),
        sa.Column('description', sa.Unicode(length = 255), nullable = True),
        sa.Column('state', sa.Enum(
            'active',
            'completed',
        ), nullable = False),
        sa.Column('due', sa.DateTime(), nullable = True),
        sa.Column('created_at', sa.DateTime(), nullable = False),
        sa.Column('completed_at', sa.DateTime(), nullable = True),
        sa.Column('modified_at', sa.DateTime(), nullable = False),
        sa.Column('display_position', sa.Unicode(length = 50), nullable = False),
    )

    op.create_table(
        'projects_contain_projects',
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable = False),
        sa.Column('child_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable = False),
        sa.PrimaryKeyConstraint('parent_id', 'child_id'),
    )

    op.create_table(
        'projects_contain_todos',
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable = False),
        sa.Column('todo_id', sa.Integer(), sa.ForeignKey('todos.id'), nullable = False),
        sa.PrimaryKeyConstraint('project_id', 'todo_id'),
    )

    op.create_table(
        'projects_prereq_projects',
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable = False),
        sa.Column('prereq_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable = False),
        sa.PrimaryKeyConstraint('project_id', 'prereq_id'),
    )

    op.create_table(
        'projects_prereq_todos',
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable = False),
        sa.Column('todo_id', sa.Integer(), sa.ForeignKey('todos.id'), nullable = False),
        sa.PrimaryKeyConstraint('project_id', 'todo_id'),
    )

    op.create_table(
        'todos_prereq_projects',
        sa.Column('todo_id', sa.Integer(), sa.ForeignKey('todos.id'), nullable = False),
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable = False),
        sa.PrimaryKeyConstraint('todo_id', 'project_id'),
    )

    op.create_table(
        'todos_prereq_todos',
        sa.Column('todo_id', sa.Integer(), sa.ForeignKey('todos.id'), nullable = False),
        sa.Column('prereq_id', sa.Integer(), sa.ForeignKey('todos.id'), nullable = False),
        sa.PrimaryKeyConstraint('todo_id', 'prereq_id'),
    )

    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), nullable = False, primary_key = True),
        sa.Column('text', sa.UnicodeText(), nullable = True),
        sa.Column('created_at', sa.DateTime(), nullable = True),
        sa.Column('modified_at', sa.DateTime(), nullable = True),
    )

    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable = False, primary_key = True),
        sa.Column('name', sa.Unicode(length = 255), nullable = False),
        sa.Column('created_at', sa.DateTime(), nullable = True),
        sa.Column('modified_at', sa.DateTime(), nullable = True),
    )

    op.create_table(
        'projects_notes',
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable = False),
        sa.Column('note_id', sa.Integer(), sa.ForeignKey('notes.id'), nullable = False),
        sa.PrimaryKeyConstraint('project_id', 'note_id'),
    )

    op.create_table(
        'todos_notes',
        sa.Column('todo_id', sa.Integer(), sa.ForeignKey('todos.id'), nullable = False),
        sa.Column('note_id', sa.Integer(), sa.ForeignKey('notes.id'), nullable = False),
        sa.PrimaryKeyConstraint('todo_id', 'note_id'),
    )

    op.create_table(
        'projects_tags',
        sa.Column('project_id', sa.Integer(), sa.ForeignKey('projects.id'), nullable = False),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id'), nullable = False),
        sa.PrimaryKeyConstraint('project_id', 'tag_id'),
    )

    op.create_table(
        'todos_tags',
        sa.Column('todo_id', sa.Integer(), sa.ForeignKey('todos.id'), nullable = False),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id'), nullable = False),
        sa.PrimaryKeyConstraint('todo_id', 'tag_id'),
    )

def downgrade():
    pass
