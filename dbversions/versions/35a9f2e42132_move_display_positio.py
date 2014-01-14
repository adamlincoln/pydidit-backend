"""Move display_position to BigInteger

Revision ID: 35a9f2e42132
Revises: df770cdad2c
Create Date: 2014-01-07 23:16:25.684184

"""

# revision identifiers, used by Alembic.
revision = '35a9f2e42132'
down_revision = 'df770cdad2c'

from alembic import op
import sqlalchemy as sa
import sqlalchemy.sql as sasql
import sqlalchemy.sql.expression as sasqlexpr

from IPython.terminal.embed import InteractiveShellEmbed
from IPython.terminal.embed import embed
from copy import copy

# Algorithm at the time of versioning
def display_position_compare(x, y):
    x = x[1]
    y = y[1]
    x_components = x.split(u'.')
    y_components = y.split(u'.')
    common_depth = 0
    final_resolution = None
    if len(x_components) > len(y_components):
        common_depth = len(x_components)
        final_resolution = 1  # See comment below
    elif len(x_components) < len(y_components):
        common_depth = len(y_components)
        final_resolution = -1  # See comment below
    else:
        common_depth = len(y_components)  # Could be either
        final_resolution = 0  # See comment below
    for i in xrange(common_depth):
        if int(x_components[i]) > int(y_components[i]):
            return -1  # x is bigger
        elif int(x_components[i]) < int(y_components[i]):
            return 1  # y is bigger
    # If i'm here, then all the common depth components are the same.
    # So we assume the longer one is bigger.
    return final_resolution

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
    
    todos.sort(cmp=lambda x, y: -display_position_compare(x, y))

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
    
    projects.sort(cmp=lambda x, y: -display_position_compare(x, y))

    if current_context.opts['driver'] == 'pysqlite':
        #ipshell = InteractiveShellEmbed()
        #ipshell.mainloop(global_ns={}, local_ns={'hi': todos_table})

        if len(todos) > 0:
            # todos
            # Make new table with column of new type
            todos_cols = [copy(todos_col) for todos_col in todos_table.c.values()]
            for todos_col in todos_cols:
                todos_col.table = None
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
                    'display_position': i,
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
                    # Convert display_position
                    'display_position': i,
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
        op.alter_column(
            'todos',
            'display_position',
            type_=sa.BigInteger(),
            existing_type=sa.Unicode(length=50),
            existing_server_default=None,
            existing_nullable=False,
        )

        if len(todos) > 0:
            todo_bind_params = []
            for i in xrange(len(todos)):
                todo_bind_params.append({'id': todos[i][0], 'display_position': i})

            todo_update_stmt = todos_table.update().where(
                todos_table.c.id == sasqlexpr.bindparam('id')
            ).values(display_position=sasqlexpr.bindparam('display_position'))

            conn.execute(todo_update_stmt, todo_bind_params)

        op.alter_column(
            'projects',
            'display_position',
            type_=sa.BigInteger(),
            existing_type=sa.Unicode(length=50),
            existing_server_default=None,
            existing_nullable=False,
        )

        if len(projects) > 0:
            project_bind_params = []
            for i in xrange(len(projects)):
                project_bind_params.append({'id': projects[i][0], 'display_position': i})

            project_update_stmt = projects_table.update().where(
                projects_table.c.id == sasqlexpr.bindparam('id')
            ).values(display_position=sasqlexpr.bindparam('display_position'))

            conn.execute(project_update_stmt, project_bind_params)

def downgrade():
    pass
