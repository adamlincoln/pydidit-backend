from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import ForeignKey

from sqlalchemy.orm import relation
from sqlalchemy.orm import backref

from Permission import Permission

from pydiditbackend.models import Base
from User import User


class WorkspacePermission(Permission, Base):
    '''Workspace Permission object'''
    __tablename__ = 'workspace_permissions'

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, primary_key=True)

    user = relation(
        'User',
        backref=backref('permissions', lazy='joined', join_depth=1, order_by='WorkspacePermission.modified_at', cascade='all, delete-orphan'),
        #secondary='workspace_permissions',
        lazy='joined',
        join_depth=1,
        order_by='User.id',
    )

    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False, primary_key=True)

    workspace = relation(
        'Workspace',
        #backref=backref('permissions', # lazy='joined', join_depth=1, order_by='WorkspacePermission.modified_at', 
            #innerjoin=True),
        #secondary='workspace_permissions',
        lazy='joined',
        join_depth=1,
        order_by='Workspace.name',
        innerjoin=True
    )

    #workspace = relation(
        #'Workspace',
        #backref=backref('read_permissions', lazy='joined', join_depth=1, order_by='Permission.modified_at'),
        ##secondary='workspace_permissions',
        #lazy='joined',
        #join_depth=1,
        #order_by='Workspace.name'
    #)

    def __repr__(self):
        return super(WorkspacePermission, self).__repr__().format(
            'User: {0}  Workspace: {1}'.format(self.user.username, self.workspace.name)
        )
