from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import Enum
from sqlalchemy import DateTime

from sqlalchemy.orm import relation
from sqlalchemy.orm import validates
from sqlalchemy.orm import backref

import pydiditbackend.models

from Model import Model

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
    display_position = Column(Unicode(length=50), nullable=False)

    prereq_projects = relation(
        'Project',
        backref=backref('dependent_todos', lazy='joined', join_depth=1),
        secondary='todos_prereq_projects',
        lazy='joined',
        join_depth=1,
    )

    prereq_todos = relation(
        'Todo',
        backref=backref('dependent_todos', lazy='joined', join_depth=1),
        secondary='todos_prereq_todos',
        primaryjoin=
                id == pydiditbackend.models.todos_prereq_todos.c.todo_id,
        secondaryjoin=
                id == pydiditbackend.models.todos_prereq_todos.c.prereq_id,
        lazy='joined',
        join_depth=1,
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

    @validates('display_position')
    def validate_display_position(self, field_name, value):
        assert len(value) <= 50
        components = value.split('.')
        for component in components:
            assert component.isdigit()
        return value

    def __str__(self):
        return '<Todo: {0} {1} {2}>'.format(self.id, self.description,
                                            self.state)
