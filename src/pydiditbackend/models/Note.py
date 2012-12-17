from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import UnicodeText
from sqlalchemy import Integer
from sqlalchemy import DateTime

import pydiditbackend.models
Base = pydiditbackend.models.Base


class Note(Base):
    '''Note object'''
    __tablename__ = 'notes'

    id = Column(Integer, autoincrement=True, nullable=False, primary_key=True)
    text = Column(UnicodeText(), nullable=True)
    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    modified_at = Column(DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now)

    def __init__(self, text=None):
        '''Create a new Note instance

        :param text:

        '''
        self.text = text

    def __str__(self):
        return '<Note: {0} {1}>'.format(self.id, self.text)
