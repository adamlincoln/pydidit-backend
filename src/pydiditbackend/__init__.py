import ConfigParser
import os
from datetime import datetime

from sqlalchemy import engine_from_config

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from zope.sqlalchemy import ZopeTransactionExtension
import transaction

from models.Todo import Todo
from models.Project import Project
from models.Tag import Tag
from models.Note import Note

from models import Base

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


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


def get(model_name, all=False, filter_by=None):
    query = DBSession.query(eval(model_name))
    if filter_by is not None:
        query = query.filter_by(**filter_by)
    else:
        if hasattr(eval(model_name), 'state') and not all:
            query = query.filter_by(state=u'active')
    if hasattr(eval(model_name), 'display_position'):
        query = query.order_by(eval(model_name).__table__.c.display_position)
    return [obj.to_dict() for obj in query.all()]


def get_like(model_dict, all=False, filter_by=None):
    return get(str(model_dict['type']), all, filter_by)


def _display_position_compare(x, y):
    x_components = x.split(u'.')
    y_components = y.split(u'.')
    common_depth = 0
    final_resolution = None
    if len(x_components) > len(y_components):
        common_depth = len(x_components)
        final_resolution = 1  # See comment below
    elif len(x_components) < len(y_components):
        common_depth = len(y_components)
        final_resolution = -1  # See comment below
    else:
        common_depth = len(y_components)  # Could be either
        final_resolution = 0  # See comment below
    for i in xrange(common_depth):
        if int(x_components[i]) > int(y_components[i]):
            return -1  # x is bigger
        elif int(x_components[i]) < int(y_components[i]):
            return 1  # y is bigger
    # If i'm here, then all the common depth components are the same.
    # So we assume the longer one is bigger.
    return final_resolution


def get_new_lowest_display_position(model_name):
    display_positions = \
        [result[0] for result in DBSession.query(eval(model_name).display_position).all()]
    display_positions.sort(_display_position_compare)
    lowest_display_position = None
    if len(display_positions) > 0:
        lowest_display_position = display_positions[0]
    else:
        lowest_display_position = u'0.0.0.0'
    position_components = lowest_display_position.split(u'.')
    new_position_components = [unicode(int(position_components[0]) + 1)]
    new_position_components.extend(
        [u'0' for component in position_components[1:]]
    )
    return u'.'.join(new_position_components)


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


def _instance_from_dict(model_dict):
    return DBSession.query(eval(model_dict['type'])).filter_by(id=model_dict['id']).one()


def _has_attribute(model_name, attribute):
    return hasattr(eval(model_name), attribute)


def delete_from_db(model_dict):
    DBSession.delete(_instance_from_dict(model_dict))
    return model_dict


def put(model_name, description_text_name, display_position=None):
    model_dict = make(model_name, description_text_name, display_position)
    return add_to_db(model_dict)


def put_like(model_dict, description_text_name):
    return put(str(model_dict['type']), description_text_name)


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


def link(parent_dict, attribute, child_dict):
    if attribute in parent_dict:
        parent_instance = _instance_from_dict(parent_dict)
        child_instance = _instance_from_dict(child_dict)
        getattr(parent_instance, attribute).append(child_instance)
        parent_dict[attribute].append(child_dict)
        return parent_dict
    return None


def commit():
    transaction.commit()


def flush():
    DBSession.flush()
