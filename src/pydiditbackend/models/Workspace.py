from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import DateTime

from sqlalchemy.orm import relation
from sqlalchemy.orm import backref

from sqlalchemy.ext.associationproxy import association_proxy

import pydiditbackend.models

Base = pydiditbackend.models.Base


class Workspace(Base):
    '''Workspace object'''
    __tablename__ = 'workspaces'

    id = Column(
        Integer,
        autoincrement=True,
        nullable=False,
        primary_key=True
    )
    name = Column(Unicode(length=255), nullable=False)
    description = Column(Unicode(length=1024), nullable=False)
    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    modified_at = Column(
        DateTime(),
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

    todos = relation(
        'Todo',
        backref=backref('workspaces', lazy='joined', join_depth=1, order_by='Workspace.name'),
        secondary='workspace_todos',
        #primaryjoin=
                #id == pydiditbackend.models.workspace_todos.c.workspace_id,
        #secondaryjoin=
                #id == pydiditbackend.models.workspace_todos.c.todo_id,
        #lazy='select',
        lazy='dynamic',
        join_depth=1,
        order_by='Todo.display_position',
    )

    projects = relation(
        'Project',
        backref=backref('workspaces', lazy='joined', join_depth=1, order_by='Workspace.name'),
        secondary='workspace_projects',
        #primaryjoin=
                #id == pydiditbackend.models.workspace_projects.c.workspace_id,
        #secondaryjoin=
                #id == pydiditbackend.models.workspace_projects.c.project_id,
        #lazy='select',
        lazy='dynamic',
        join_depth=1,
        order_by='Project.display_position',
    )

    tags = relation(
        'Tag',
        backref=backref('workspaces', lazy='joined', join_depth=1, order_by='Workspace.name'),
        secondary='workspace_tags',
        #primaryjoin=
                #id == pydiditbackend.models.workspace_tags.c.workspace_id,
        #secondaryjoin=
                #id == pydiditbackend.models.workspace_tags.c.tag_id,
        #lazy='select',
        lazy='dynamic',
        join_depth=1,
        order_by='Tag.name',
    )

    notes = relation(
        'Note',
        backref=backref('workspaces', lazy='joined', join_depth=1, order_by='Workspace.name'),
        secondary='workspace_notes',
        #primaryjoin=
                #id == pydiditbackend.models.workspace_notes.c.workspace_id,
        #secondaryjoin=
                #id == pydiditbackend.models.workspace_notes.c.note_id,
        #lazy='select',
        lazy='dynamic',
        join_depth=1,
        order_by='Note.modified_at',
    )

    permissions = relation(
        'WorkspacePermission',
        #secondary='workspace_permissions',
        lazy='joined',
        join_depth=1,
        order_by='Workspace.name',
        innerjoin=True
    )

    @property
    def read_permissions(self):
        return [permission for permission in self.permissions if permission.read]

    @property
    def write_permissions(self):
        return [permission for permission in self.permissions if permission.write]

    @property
    def delete_permissions(self):
        return [permission for permission in self.permissions if permission.delete]

    def can_read(self, user_id):
        for permission in self.read_permissions:
            if permission.read and permission.user_id == user_id:
                return True
        return False

    def can_write(self, user_id):
        for permission in self.write_permissions:
            if permission.write and permission.user_id == user_id:
                return True
        return False

    def can_delete(self, user_id):
        for permission in self.delete_permissions:
            if permission.delete and permission.user_id == user_id:
                return True
        return False

    def __init__(self, name, description):
        '''Create a new Workspace

        :param name:
        :param description:

        '''
        self.name = name
        self.description = description

    def __str__(self):
        return '<Workspace: {0} {1}>'.format(self.id, self.name)

    def __repr__(self):
        return str(self)
