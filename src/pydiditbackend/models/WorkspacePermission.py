from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import ForeignKey
from sqlalchemy import Boolean
from sqlalchemy import DateTime

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
        lazy='joined',
        join_depth=1,
        order_by='User.id',
    )

    workspace_id = Column(Integer, ForeignKey('workspaces.id'), nullable=False, primary_key=True)

    workspace = relation(
        'Workspace',
        lazy='joined',
        join_depth=1,
        order_by='Workspace.name',
        innerjoin=True
    )

    def __init__(self, **kwargs):
        from pydiditbackend import DBSession
        super(WorkspacePermission, self).__init__(**kwargs)
        if 'user_id' in kwargs:
            self.user = DBSession.query(User).filter_by(id=kwargs['user_id']).one()

    def __repr__(self):
        enabled_permissions = []
        for perm in ('read', 'write', 'delete'):
            if getattr(self, perm):
                enabled_permissions.append(perm)

        return super(WorkspacePermission, self).__repr__().format(
            'User: {0}  Workspace: {1}'.format(self.user.username, self.workspace.name)
        )
