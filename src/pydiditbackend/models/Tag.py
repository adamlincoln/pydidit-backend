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

    @staticmethod
    def create(tag_names):
        if isinstance(tag_names, basestring):
            tag_names = [tag_names]

        new_tags = []
        for tag_name in tag_names:
            new_tag = Tag(tag_name)
            new_tags.append(new_tag)

        return new_tags

    def __init__(self, name=None):
        '''Create a new Tag instance

        :param text:

        '''
        self.name = name

    def __str__(self):
        return '<Tag: {0} {1}>'.format(self.id, self.name)

    def get_primary_descriptor(self):
        return Tag.primary_descriptor()

    @staticmethod
    def primary_descriptor():
        return 'name'
