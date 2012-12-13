from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import Column
from sqlalchemy import Table

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Association tables

projects_contain_projects = Table('projects_contain_projects', Base.metadata,
    Column('parent_id', Integer(), ForeignKey('projects.id'), nullable = False),
    Column('child_id', Integer(), ForeignKey('projects.id'), nullable = False),
    PrimaryKeyConstraint('parent_id', 'child_id'),
)

projects_contain_todos = Table('projects_contain_todos', Base.metadata,
    Column('project_id', Integer(), ForeignKey('projects.id'), nullable = False),
    Column('todo_id', Integer(), ForeignKey('todos.id'), nullable = False),
    PrimaryKeyConstraint('project_id', 'todo_id'),
)

projects_prereq_projects = Table('projects_prereq_projects', Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id'), nullable = False),
    Column('prereq_id', Integer, ForeignKey('projects.id'), nullable = False),
    PrimaryKeyConstraint('project_id', 'prereq_id'),
)

projects_prereq_todos = Table('projects_prereq_todos', Base.metadata,
    Column('project_id', Integer(), ForeignKey('projects.id'), nullable = False),
    Column('todo_id', Integer(), ForeignKey('todos.id'), nullable = False),
    PrimaryKeyConstraint('project_id', 'todo_id'),
)

todos_prereq_projects = Table('todos_prereq_projects', Base.metadata,
    Column('todo_id', Integer, ForeignKey('todos.id'), nullable = False),
    Column('project_id', Integer, ForeignKey('projects.id'), nullable = False),
    PrimaryKeyConstraint('todo_id', 'project_id')
)

todos_prereq_todos = Table('todos_prereq_todos', Base.metadata,
    Column('todo_id', Integer(), ForeignKey('todos.id'), nullable = False),
    Column('prereq_id', Integer(), ForeignKey('todos.id'), nullable = False),
    PrimaryKeyConstraint('todo_id', 'prereq_id'),
)

projects_notes = Table('projects_notes', Base.metadata,
    Column('project_id', Integer(), ForeignKey('projects.id'), nullable = False),
    Column('note_id', Integer(), ForeignKey('notes.id'), nullable = False),
    PrimaryKeyConstraint('project_id', 'note_id'),
)

todos_notes = Table('todos_notes', Base.metadata,
    Column('todo_id', Integer(), ForeignKey('todos.id'), nullable = False),
    Column('note_id', Integer(), ForeignKey('notes.id'), nullable = False),
    PrimaryKeyConstraint('todo_id', 'note_id'),
)

projects_tags = Table('projects_tags', Base.metadata,
    Column('project_id', Integer(), ForeignKey('projects.id'), nullable = False),
    Column('tag_id', Integer(), ForeignKey('tags.id'), nullable = False),
    PrimaryKeyConstraint('project_id', 'tag_id'),
)

todos_tags = Table('todos_tags', Base.metadata,
    Column('todo_id', Integer(), ForeignKey('todos.id'), nullable = False),
    Column('tag_id', Integer(), ForeignKey('tags.id'), nullable = False),
    PrimaryKeyConstraint('todo_id', 'tag_id'),
)

