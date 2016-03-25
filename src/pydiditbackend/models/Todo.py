from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import BigInteger
from sqlalchemy import Enum
from sqlalchemy import DateTime

from sqlalchemy.orm import relation
from sqlalchemy.orm import validates
from sqlalchemy.orm import backref

import pydiditbackend.models

from Model import Model
from Workspace import Workspace

Base = pydiditbackend.models.Base


class Todo(Model, Base):
    '''Todo object'''
    __tablename__ = 'todos'

    id = Column(
        Integer,
        autoincrement=True,
        nullable=False,
        primary_key=True
    )
    description = Column(Unicode(length=255), nullable=False)
    state = Column(Enum(
        'active',
        'completed',
    ), nullable=False)
    due = Column(DateTime(), nullable=True)
    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    completed_at = Column(DateTime(), nullable=True)
    modified_at = Column(
        DateTime(),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )
    show_from = Column(DateTime(), nullable=True)
    display_position = Column(BigInteger(), nullable=False)

    prereq_projects = relation(
        'Project',
        backref=backref('dependent_todos', lazy='joined', join_depth=1, order_by='Todo.display_position'),
        secondary='todos_prereq_projects',
        lazy='joined',
        join_depth=1,
        order_by='Project.display_position',
    )

    prereq_todos = relation(
        'Todo',
        backref=backref('dependent_todos', lazy='joined', join_depth=1, order_by='Todo.display_position'),
        secondary='todos_prereq_todos',
        primaryjoin=
                id == pydiditbackend.models.todos_prereq_todos.c.todo_id,
        secondaryjoin=
                id == pydiditbackend.models.todos_prereq_todos.c.prereq_id,
        lazy='joined',
        join_depth=1,
        order_by='Todo.display_position',
    )

    notes = relation(
        'Note',
        backref=backref('todos', lazy='joined', join_depth=1),
        secondary='todos_notes',
        lazy='joined',
        join_depth=1,
    )

    tags = relation(
        'Tag',
        backref=backref('todos', lazy='joined', join_depth=1),
        secondary='todos_tags',
        lazy='joined',
        join_depth=1,
    )

    @staticmethod
    def create(*args):
        todo_datas = []
        if len(args) == 1:
            # Then we expect an iterable of 2-tuples:
            # ('description', integer display position)
            todo_datas = args[0]
        if len(args) == 2:
            # Then we expect one iterable of descriptions and another of
            # display_positions.  Alternatively, they could both be scalars
            descriptions = args[0]
            display_positions = args[1]
            if isinstance(descriptions, basestring):
                descriptions = [descriptions]
            if isinstance(display_positions, int):
                display_positions = [display_positions]
            todo_datas = zip(descriptions, display_positions)

        new_todos = []
        for todo_data in todo_datas:
            new_todo = Todo(todo_data[0], todo_data[1])
            new_todos.append(new_todo)

        return new_todos

    def __init__(self, description, display_position, state=u'active',
                 due=None, show_from=None):
        '''Create a new Todo instance

        :param description:
        :param display_position:

        :param state: 'active' or 'completed', optional (defaults to 'active')
        :param due: Due date, optional
        :param show_from: Ignore until specified date, optional

        '''
        self.description = description
        self.display_position = display_position
        self.state = state
        self.due = due
        self.show_from = show_from

    #@validates('display_position')
    #def validate_display_position(self, field_name, value):
        #assert len(value) <= 50
        #components = value.split('.')
        #for component in components:
            #assert component.isdigit()
        #return value

    def __str__(self):
        return '<Todo: {0} {1} {2} {3}>'.format(self.id, self.description,
                                            self.state, str(self.display_position))

    def __repr__(self):
        return str(self)

    def get_primary_descriptor(self):
        return Todo.primary_descriptor()

    @staticmethod
    def primary_descriptor():
        return 'description'
