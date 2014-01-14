import ConfigParser
import os
from datetime import datetime

from sqlalchemy import engine_from_config

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.inspection import inspect

from zope.sqlalchemy import ZopeTransactionExtension
import transaction

from models.Todo import Todo
from models.Project import Project
from models.Tag import Tag
from models.Note import Note

from models import Base

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))

import logging
log = logging.getLogger(__name__)

def initialize(ini_filenames=(os.path.expanduser('~/.pydiditrc'),
                              os.path.expanduser('~/.pydidit-backendrc')),
               external_config_fp=None):
    ini = ConfigParser.SafeConfigParser()
    ini.read(ini_filenames)
    allow_external_config = ini.getboolean('backend', 'allow_external_config')
    if allow_external_config is True and external_config_fp is not None:
        ini.readfp(external_config_fp)
    settings = dict(ini.items('backend'))

    engine = engine_from_config(settings, 'sqlalchemy.')
    Base.metadata.bind = engine
    DBSession.configure(bind=engine)


# Start stuff for reading

def get(model_name, all=False, filter_by=None):
    query = DBSession.query(eval(model_name))
    if filter_by is not None:
        query = query.filter_by(**filter_by)
    else:
        if hasattr(eval(model_name), 'state') and not all:
            query = query.filter_by(state=u'active')
    if hasattr(eval(model_name), 'display_position'):
        query = query.order_by(eval(model_name).display_position)
    results = query.all()
    return [obj.to_dict() for obj in results]


def get_like(model_dict, all=False, filter_by=None):
    return get(str(model_dict['type']), all, filter_by)


# End stuff for reading

# Start stuff for creating

def get_new_lowest_display_position(model_name):
    display_positions = \
        [result[0] for result in DBSession.query(eval(model_name).display_position).order_by(eval(model_name).display_position).all()]
    return display_positions[-1] + 1


def make(model_name, description_text_name, display_position=None):
    model_dict = {
        'type': model_name
    }
    model = eval(model_name)

    if hasattr(model, 'description'):
        model_dict['description'] = description_text_name
    elif hasattr(model, 'text'):
        model_dict['text'] = description_text_name
    elif hasattr(model, 'name'):
        model_dict['name'] = description_text_name

    if hasattr(model, 'display_position'):
        if display_position is None:
            model_dict['display_position'] = get_new_lowest_display_position(model_name)
        else:
            model_dict['display_position'] = display_position

    return model_dict


def make_like(model_dict, description_text_name, display_position=None):
    return make(model_dict['type'], description_text_name, display_position)


def add_to_db(model_dict):
    new_instance_parameters = []
    if 'description' in model_dict:
        new_instance_parameters.append(model_dict['description'])
    elif 'name' in model_dict:
        new_instance_parameters.append(model_dict['name'])
    elif 'text' in model_dict:
        new_instance_parameters.append(model_dict['text'])

    if 'display_position' in model_dict:
        new_instance_parameters.append(model_dict['display_position'])

    new_instance = eval(model_dict['type'])(*new_instance_parameters)
    for key, value in model_dict.iteritems():
        if key not in ('description', 'name', 'text', 'display_position'):
            setattr(new_instance, key, value)

    DBSession.add(new_instance)
    flush()
    model_dict['id'] = new_instance.id
    return model_dict


def put(model_name, description_text_name, display_position=None):
    model_dict = make(model_name, description_text_name, display_position)
    return add_to_db(model_dict)


def put_like(model_dict, description_text_name):
    return put(str(model_dict['type']), description_text_name)


# End stuff for creating

# Start utilities

def _instance_from_dict(model_dict):
    return DBSession.query(eval(model_dict['type'])).filter_by(id=model_dict['id']).one()

def _has_attribute(model_name, attribute):
    return hasattr(eval(model_name), attribute)

def commit():
    transaction.commit()

def flush():
    DBSession.flush() 

# End utilities

# Start stuff for deleting

def delete_from_db(model_dict):
    DBSession.delete(_instance_from_dict(model_dict))
    return model_dict

# End stuff for deleting

# Start stuff for updating

def set_completed(model_dict):
    if _has_attribute(model_dict['type'], 'completed_at'):
        model_dict['state'] = u'completed'
        model_dict['completed_at'] = datetime.now()
        if 'id' in model_dict:
            instance = _instance_from_dict(model_dict)
            if hasattr(instance, 'state'):
                instance.state = u'completed'
            if hasattr(instance, 'completed_at'):
                instance.completed_at = datetime.now()
        return model_dict
    else:
        return None

def set_attributes(model_dict, new_values):
    model_instance = None
    if 'id' in model_dict:
        model_instance = _instance_from_dict(model_dict)
    for attribute, value in new_values.iteritems():
        _set_attribute(model_instance, model_dict, attribute, value)
    return model_dict

def _set_attribute(model_instance, model_dict, attribute, value):
    if attribute in model_dict:
        model_dict[attribute] = value
        if model_instance is not None and hasattr(model_instance, attribute):
            setattr(model_instance, attribute, value)

def swap_display_positions(model_dict_one, model_dict_two):
    if 'display_position' in model_dict_one and \
       'display_position' in model_dict_two and \
       model_dict_one['type'] == model_dict_two['type']:

        temp = model_dict_one['display_position']
        set_attributes(model_dict_one, {'display_position': model_dict_two['display_position']})
        set_attributes(model_dict_two, {'display_position': temp})

        return [model_dict_one, model_dict_two]

# End stuff for updating

# Start stuff for relationships

def relationship_name(parent_type, child_type, *args, **kwargs):
    if 'prereq' in args or ('prereq' in kwargs and kwargs['prereq']): # special cases
        if parent_type == 'Project':
            if child_type == 'Project':
                return 'prereq_projects'
            elif child_type == 'Todo':
                return 'prereq_todos'
        elif parent_type == 'Todo':
            if child_type == 'Project':
                return 'prereq_projects'
            elif child_type == 'Todo':
                return 'prereq_todos'
        return attribute
    if 'dependent' in args or ('dependent' in kwargs and kwargs['dependent']): # special cases
        if parent_type == 'Project':
            if child_type == 'Project':
                return 'dependent_projects'
            elif child_type == 'Todo':
                return 'dependent_todos'
        elif parent_type == 'Todo':
            if child_type == 'Project':
                return 'dependent_projects'
            elif child_type == 'Todo':
                return 'dependent_todos'
        return attribute
    elif 'contain' in args or ('contain' in kwargs and kwargs['contain']):
        if parent_type == 'Project':
            if child_type == 'Project':
                return 'contains_projects'
            elif child_type == 'Todo':
                return 'contains_todos'
    elif 'contained_by' in args or ('contained_by' in kwargs and kwargs['contained_by']):
        if parent_type == 'Project':
            if child_type == 'Project':
                return 'contained_by_projects'
        if parent_type == 'Todo':
            if child_type == 'Project':
                return 'contained_by_projects'

    # Non-special cases
    potential_relationships = []
    for relationship_name in inspect(eval(parent_type)).mapper.relationships.keys():
        if child_type == inspect(eval(parent_type)).mapper.relationships[relationship_name].mapper.class_.__name__:
            # Might this trigger on relationships we don't want?
            potential_relationships.append({relationship_name: (parent_type, child_type)})

    if len(potential_relationships) != 1:
        raise Exception('Something is wrong.')
    else:
        return potential_relationships[0].keys()[0]

def link(parent_dict, child_dict, *args, **kwargs):
    attribute = relationship_name(parent_dict['type'], child_dict['type'], *args, **kwargs)
    if attribute is None:
        raise Exception('Cannot find the attribute to link the child to the parent.')

    parent_instance = _instance_from_dict(parent_dict)
    child_instance = _instance_from_dict(child_dict)
    if 'unlink' in kwargs and kwargs['unlink']:
        getattr(parent_instance, attribute).remove(child_instance)
    else:
        getattr(parent_instance, attribute).append(child_instance)
    parent_dict[attribute].append(child_dict)
    return parent_dict

def unlink(parent_dict, child_dict, *args, **kwargs):
    kwargs['unlink'] = True
    return link(parent_dict, child_dict, *args, **kwargs)

# Start stuff for relationships
