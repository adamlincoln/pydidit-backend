from datetime import datetime

from sqlalchemy import Column
from sqlalchemy import Unicode
from sqlalchemy import Integer
from sqlalchemy import Enum
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

class Project(Base):
    '''Project object'''
    __tablename__ = 'projects'

    id = Column(Integer, autoincrement = True, nullable = False, primary_key = True)
    description = Column(Unicode(length = 255), nullable = True)
    state = Column(Enum(
        'active',
        'completed',
    ), nullable = False)
    due = Column(DateTime(), nullable = True)
    created_at = Column(DateTime(), nullable = False, default = datetime.now)
    completed_at = Column(DateTime(), nullable = True)
    modified_at = Column(DateTime(), nullable = False, onupdate = datetime.now)
    display_position = Column(Unicode(length = 50), nullable = False)

    prereq_projects = relation('Project',
        backref = 'dependent_projects',
        secondary = 'projects_prereq_projects',
        primaryjoin = id == pydiditbackend.models.projects_prereq_projects.c.project_id,
        secondaryjoin = id == pydiditbackend.models.projects_prereq_projects.c.prereq_id,
    )

    child_projects = relation('Project',
        backref = 'parent_projects',
        secondary = 'projects_contain_projects',
        primaryjoin = id == pydiditbackend.models.projects_contain_projects.c.parent_id,
        secondaryjoin = id == pydiditbackend.models.projects_contain_projects.c.child_id,
    )

    child_todos = relation('Todo',
        backref = 'parent_projects',
        secondary = 'projects_contain_todos',
    )

    notes  =  relation('Note',
        backref = 'projects',
        secondary = 'projects_notes',
    )

    tags  =  relation('Tag',
        backref = 'projects',
        secondary = 'projects_tags',
    )

    def __init__(self, description, state=u'active', due=None, show_from=None):
        '''Create a new Project instance

        :param description:

        :param state: 'active' or 'completed', optional (defaults to 'active')
        :param due: Due date, optional

        '''
        self.description = description
        self.state = state

        self.due = due

    def set_completed(self):
        self.state = 'completed'
        self.completed_at = datetime.now()

    def __str__(self):
        return '<Project: {0} {1}>'.format(self.id, self.description)

