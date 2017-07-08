from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy.sql.expression import false

from pydiditbackend.models.Model import Model

class Permission(Model):
    '''Permission object'''

    read = Column(Boolean, nullable=False, default=False)
    write = Column(Boolean, nullable=False, default=False)
    delete = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
    modified_at = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

    def __repr__(self):
        enabled_permissions = []
        for perm in ('read', 'write', 'delete'):
            if getattr(self, perm):
                enabled_permissions.append(perm)

        return '<{0}: {1}  {{0}}>'.format(
            self.__class__.__name__,
            ' '.join(enabled_permissions) if len(enabled_permissions) > 0 else 'None'
        )
