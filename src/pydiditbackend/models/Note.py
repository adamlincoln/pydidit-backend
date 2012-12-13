from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import UnicodeText
from sqlalchemy import Integer
from sqlalchemy import DateTime

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relation

#from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension

#DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
#Base = declarative_base()
import pydiditbackend.models
Base = pydiditbackend.models.Base

class Note(Base):
    '''Note object'''
    __tablename__ = 'notes'

    id = Column(Integer, autoincrement = True, nullable = False, primary_key = True)
    text = Column(UnicodeText(), nullable = True)
    created_at = Column(DateTime(), nullable = False, default = datetime.now)
    modified_at = Column(DateTime(), nullable = False, onupdate = datetime.now)

    def __init__(self, text=None):
        '''Create a new Note instance

        :param text:

        '''
        self.text = text

    def __str__(self):
        return '<Note: {0} {1}>'.format(self.id, self.text)

