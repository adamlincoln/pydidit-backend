"""Add uniqueness constraint to display_position columns

Revision ID: 26ad87352314
Revises: 35a9f2e42132
Create Date: 2014-01-17 21:59:42.640697

"""

# revision identifiers, used by Alembic.
revision = '26ad87352314'
down_revision = '35a9f2e42132'

from alembic import op
import sqlalchemy as sa
import sqlalchemy.sql as sasql
import sqlalchemy.sql.expression as sasqlexpr

from copy import copy

def upgrade():
    current_context = op.get_context()
    meta = current_context.opts['target_metadata']
    todos_table = sa.Table('todos', meta, autoload=True)
    projects_table = sa.Table('projects', meta, autoload=True)
    conn = op.get_bind()

    todos_select_stmt = sasql.select([
        todos_table.c.id,
        todos_table.c.display_position,
        todos_table.c.description,
        todos_table.c.state,
        todos_table.c.due,
        todos_table.c.created_at,
        todos_table.c.completed_at,
        todos_table.c.modified_at,
        todos_table.c.show_from
    ])
    todos = conn.execute(
        todos_select_stmt
    ).fetchall()
    
    projects_select_stmt = sasql.select([
        projects_table.c.id,
        projects_table.c.display_position,
        projects_table.c.description,
        projects_table.c.state,
        projects_table.c.due,
        projects_table.c.created_at,
        projects_table.c.completed_at,
        projects_table.c.modified_at
    ])
    projects = conn.execute(
        projects_select_stmt
    ).fetchall()

    if current_context.opts['driver'] == 'pysqlite':
        if len(todos) > 0:
            # todos
            # Make new table
            todos_cols = [copy(todos_col) for todos_col in todos_table.c.values()]
            for todos_col in todos_cols:
                todos_col.table = None
                if todos_col.name == 'display_position':
                    todos_col.unique = True
            op.create_table(
                'todos_new',
                *todos_cols
            )
            todos_new_table = sa.Table('todos_new', meta, autoload=True)

            # Migrate data
            new_todos_data = []
            for i in xrange(len(todos)):
                new_todos_data.append({
                    'id': todos[i][0],
                    # Convert display_position
                    'display_position': todos[i][1],
                    'description': todos[i][2],
                    'state': todos[i][3],
                    'due': todos[i][4],
                    'created_at': todos[i][5],
                    'completed_at': todos[i][6],
                    'modified_at': todos[i][7],
                    'show_from': todos[i][8]
                })

            conn.execute(todos_new_table.insert(), new_todos_data)

            # Drop old table
            op.drop_table('todos')

            # Rename new table to desired name
            op.rename_table('todos_new', 'todos')

        if len(projects) > 0:
            # projects
            # Make new table with column of new type
            projects_cols = [copy(projects_col) for projects_col in projects_table.c.values()]
            for projects_col in projects_cols:
                projects_col.table = None
                if projects_col.name == 'display_position':
                    projects_col.unique = True
            op.create_table(
                'projects_new',
                *projects_cols
            )
            projects_new_table = sa.Table('projects_new', meta, autoload=True)

            # Migrate data
            new_projects_data = []
            for i in xrange(len(projects)):
                new_projects_data.append({
                    'id': projects[i][0],
                    'display_position': projects[i][1],
                    'description': projects[i][2],
                    'state': projects[i][3],
                    'due': projects[i][4],
                    'created_at': projects[i][5],
                    'completed_at': projects[i][6],
                    'modified_at': projects[i][7]
                })

            conn.execute(projects_new_table.insert(), new_projects_data)

            # Drop old table
            op.drop_table('projects')

            # Rename new table to desired name
            op.rename_table('projects_new', 'projects')

    else:
        op.create_unique_constraint(None, "todos", ["display_position"])
        op.create_unique_constraint(None, "projects", ["display_position"])


def downgrade():
    pass
