import ConfigParser
import datetime
import os

#from sqlalchemy import create_engine
from sqlalchemy import engine_from_config
from sqlalchemy import desc

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relation

from sqlalchemy.ext.declarative import declarative_base

from zope.sqlalchemy import ZopeTransactionExtension
import transaction

from models.Todo import Todo
from models.Project import Project
from models.Note import Note
from models.Tag import Tag

from models import Base

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

def initialize(ini_filenames=(os.path.expanduser('~/.pydiditrc'), os.path.expanduser('~/.pydidit-backendrc')), external_config_fp=None):
    ini = ConfigParser.SafeConfigParser()
    ini.read(ini_filenames)
    allow_external_config = ini.getboolean('backend', 'allow_external_config')
    if allow_external_config == True and external_config_fp is not None:
        ini.readfp(external_config_fp)
    settings = dict(ini.items('backend'))

    engine = engine_from_config(settings, 'sqlalchemy.')
    Base.metadata.bind = engine
    DBSession.configure(bind = engine)

def get(model_name, all=False, filter_by=None):
    query = eval('DBSession.query({0})'.format(model_name))
    if filter_by is not None:
        query = query.filter_by(**filter_by)
    else:
        if eval("hasattr({0}, u'state')".format(model_name)) and not all:
            query = query.filter_by(state = u'active')
    return query.all()
        
def get_like(model_instance, all=False, filter_by=None):
    return get(str(model_instance.__class__), all, filter_by)

def _display_position_compare(x, y):
    x_components = x.split(u'.')
    y_components = y.split(u'.')
    common_depth = 0
    final_winner = None
    if len(x_components) > len(y_components):
        common_depth = len(x_components)
        final_resolution = 1 # See comment below
    elif len(x_components) < len(y_components):
        common_depth = len(y_components)
        final_resolution = -1 # See comment below
    else:
        common_depth = len(y_components) # Could be either
        final_resolution = 0 # See comment below
    for i in xrange(common_depth):
        if int(x_components[i]) > int(y_components[i]):
            return -1 # x is bigger
        elif int(x_components[i]) < int(y_components[i]):
            return 1 # y is bigger
    # If i'm here, then all the common depth components are the same.
    # So we assume the longer one is bigger.
    return final_resolution

def get_new_lowest_display_position():
    display_positions = [result[0] for result in DBSession.query(Todo.display_position).all()]
    display_positions.sort(_display_position_compare)
    lowest_display_position = None
    if len(display_positions) > 0:
        lowest_display_position = display_positions[0]
    else:
        lowest_display_position = u'0.0.0.0'
    position_components = lowest_display_position.split(u'.')
    new_position_components = [unicode(int(position_components[0]) + 1)]
    new_position_components.extend([u'0' for component in position_components[1:]])
    return u'.'.join(new_position_components)
    #return u'.'.join((unicode(int(position_components[0]) + 1), *([u'0' for component in position_components[1:]])))

def make(model_name, description_text_name, display_position=None):
    parameters = [description_text_name]
    if model_name == 'Todo':
        if display_position is None:
            parameters.append(get_new_lowest_display_position())
        else:
            parameters.append(display_position)
    new_instance = eval("{0}(u'{1}')".format(model_name, "',u'".join(parameters)))
    return new_instance

def make_like(model_instance, description_text_name):
    return make(str(model_instance.__class__), description_text_name)

def add_to_db(model_instance):
    DBSession.add(model_instance)
    return model_instance

def delete_from_db(model_instance):
    DBSession.delete(model_instance)
    return model_instance

def put(model_name, description_text_name, display_position=None):
    new_instance = make(model_name, description_text_name, display_position)
    return add_to_db(new_instance)

def put_like(model_instance, description_text_name):
    return put(str(model_instance.__class__), description_text_name)

def commit():
    transaction.commit()

