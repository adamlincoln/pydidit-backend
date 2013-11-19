from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import DateTime

import pydiditbackend.models
from pydiditbackend.models.Model import Model
Base = pydiditbackend.models.Base

# Example package with a console entry point


class Tag(Model, Base):
    '''Tag object'''
    __tablename__ = 'tags'

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    name = Column(Unicode(length=255), nullable=True)
    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    modified_at = Column(DateTime(), nullable=False, default=datetime.now,
                         onupdate=datetime.now)

    def __init__(self, name=None):
        '''Create a new Tag instance

        :param text:

        '''
        self.name = name

    def __str__(self):
        return '<Tag: {0} {1}>'.format(self.id, self.name)

    def primary_descriptor(self):
        return 'name'
