"""Add Authorization

Revision ID: 3956b7b6142b
Revises: 26ad87352314
Create Date: 2015-05-12 02:33:40.949276

"""

# revision identifiers, used by Alembic.
revision = '3956b7b6142b'
down_revision = '26ad87352314'

from alembic import op
import sqlalchemy as sa
import sqlalchemy.sql as sasql

from datetime import datetime

debug = False

def upgrade():
    current_context = op.get_context()
    meta = current_context.opts['target_metadata']
    conn = op.get_bind()

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('username', sa.Unicode(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('name', sa.Unicode(length=255), nullable=False),
        sa.Column('description', sa.Unicode(length=1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'workspace_permissions',
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False),
        sa.Column('write', sa.Boolean(), nullable=False),
        sa.Column('delete', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'todo_permissions',
        sa.Column('todo_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False),
        sa.Column('write', sa.Boolean(), nullable=False),
        sa.Column('delete', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'project_permissions',
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False),
        sa.Column('write', sa.Boolean(), nullable=False),
        sa.Column('delete', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'tag_permissions',
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False),
        sa.Column('write', sa.Boolean(), nullable=False),
        sa.Column('delete', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'note_permissions',
        sa.Column('note_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False),
        sa.Column('write', sa.Boolean(), nullable=False),
        sa.Column('delete', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'workspace_todos',
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('todo_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'workspace_projects',
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'workspace_tags',
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    op.create_table(
        'workspace_notes',
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('note_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('modified_at', sa.DateTime(), nullable=False)
    )

    now = datetime.now()
    users_table = sa.Table('users', meta, autoload=True)
    conn.execute(users_table.insert(), [{
        'id': 0,
        'username': 'admin',
        'created_at': now,
        'modified_at': now,
    }])

    workspaces_table = sa.Table('workspaces', meta, autoload=True)
    conn.execute(workspaces_table.insert(), [{
        'id': 0,
        'name': 'Default',
        'created_at': now,
        'modified_at': now,
    }])


    # Put all todos in default workspace
    todos_table = sa.Table('todos', meta, autoload=True)
    todos_select_stmt = sasql.select([
        todos_table.c.id,
    ])
    todos = conn.execute(
        todos_select_stmt
    ).fetchall()

    if len(todos) == 0 and debug:
        conn.execute(todos_table.insert(), [{
            'id': 0,
            'display_position': 0,
            'description': u'placeholder todo',
            'state': u'active',
            'created_at': now,
            'modified_at': now
        }])
        todos = conn.execute(
            todos_select_stmt
        ).fetchall()
        
    if len(todos) > 0:
        new_workspace_todos = []
        for todo in todos:
            new_workspace_todos.append({
                'workspace_id': 0,
                'todo_id': todo.id,
                'created_at': now,
                'modified_at': now
            })

        workspace_todos_table = sa.Table('workspace_todos', meta, autoload=True)
        conn.execute(workspace_todos_table.insert(), new_workspace_todos)


    # Add initial permissions
    workspace_permissions_table = sa.Table('workspace_permissions', meta, autoload=True)
    conn.execute(workspace_permissions_table.insert(), [
        {
            'workspace_id': 0,
            'user_id': 0,
            'read': True,
            'write': True,
            'delete': True,
            'created_at': now,
            'modified_at': now
        }
    ])

    # TODO: to implement 'send this top level thing to someone else so they can work on it but can't change/delete it', use new 'one time' workspace

    # HEREHERE FIXME: what's the authorization model?
    # - workspace
    # - top level record
    # each have these permissions:
    # - read
    # - edit
    # - delete (should this be different from edit? I think so, because i might want to delegate but i don't want my stuff to just disappear)
    # Looks like regular old CRUD.
    # 
    

'''
    if current_context.opts['driver'] == 'pysqlite':
        # todos
        # Make new table with column of new type
        todos_cols = [copy(todos_col) for todos_col in todos_table.c.values() if todos_col.name != 'display_position']
        todos_cols.append(sa.Column('display_position', sa.BigInteger(), nullable=False))
        for todos_col in todos_cols:
            todos_col.table = None
        op.create_table(
            'todos_new',
            *todos_cols
        )
        todos_new_table = sa.Table('todos_new', meta, autoload=True)

        if len(todos) > 0:
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

    else:
        op.add_column(
            'todos',
            sa.Column(
                'user_id',
                sa.Integer(),
                sa.ForeignKey('users.id'),
                nullable=False,
                server_default='0'  # alembic just puts this string in the DDL
            )
        )

        op.add_column(
            'projects',
            sa.Column(
                'user_id',
                sa.Integer(),
                sa.ForeignKey('users.id'),
                nullable=False,
                server_default='0'  # alembic just puts this string in the DDL
            )
        )

        op.add_column(
            'tags',
            sa.Column(
                'user_id',
                sa.Integer(),
                sa.ForeignKey('users.id'),
                nullable=False,
                server_default='0'  # alembic just puts this string in the DDL
            )
        )

        op.add_column(
            'notes',
            sa.Column(
                'user_id',
                sa.Integer(),
                sa.ForeignKey('users.id'),
                nullable=False,
                server_default='0'  # alembic just puts this string in the DDL
            )
        )
'''

def downgrade():
    pass
