import ConfigParser
import os
from datetime import datetime

from sqlalchemy import engine_from_config
from sqlalchemy import and_
from sqlalchemy import or_

from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.inspection import inspect

from zope.sqlalchemy import register
import transaction

from models.Todo import Todo
from models.Project import Project
from models.Tag import Tag
from models.Note import Note

from models import Base

DBSession = scoped_session(sessionmaker())
register(DBSession, keep_session=True)

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
    return 0 if not display_positions else int(display_positions[-1]) + 1


def make(model_name, description_text_name, display_position=None):
    model = eval(model_name)

    return_single = False
    model_dicts = []
    if isinstance(description_text_name, basestring):
        description_text_name = [description_text_name]
        return_single = True
    for info in description_text_name:
        model_dict = {
            'type': model_name
        }
        if hasattr(model, 'description'):
            model_dict['description'] = info 
        elif hasattr(model, 'text'):
            model_dict['text'] = info
        elif hasattr(model, 'name'):
            model_dict['name'] = info

        if hasattr(model, 'display_position'):
            if display_position is None:
                model_dict['display_position'] = get_new_lowest_display_position(model_name)
            else:
                model_dict['display_position'] = display_position

        if return_single:
            return model_dict
        else:
            model_dicts.append(model_dict)

    return model_dicts


def make_like(model_dict, description_text_name, display_position=None):
    return make(model_dict['type'], description_text_name, display_position)


def add_to_db(model_dict):
    return_single = False
    new_instances = []
    if isinstance(model_dict, dict):
        model_dict = [model_dict]
        return_single = True
    for single_model_dict in model_dict:
        new_instance_parameters = []
        if 'description' in single_model_dict:
            new_instance_parameters.append(single_model_dict['description'])
        elif 'name' in single_model_dict:
            new_instance_parameters.append(single_model_dict['name'])
        elif 'text' in single_model_dict:
            new_instance_parameters.append(single_model_dict['text'])

        if 'display_position' in single_model_dict:
            new_instance_parameters.append(single_model_dict['display_position'])

        new_instance = eval(single_model_dict['type'])(*new_instance_parameters)
        for key, value in single_model_dict.iteritems():
            if key not in ('description', 'name', 'text', 'display_position'):
                setattr(new_instance, key, value)

        new_instances.append(new_instance)

    DBSession.add_all(new_instances)
    flush()
    for i in xrange(len(new_instances)):
        model_dict[i]['id'] = new_instances[i].id

    return model_dict[0] if return_single else model_dict


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
    DBSession.close()

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

# End stuff for relationships

# Start stuff for moving

def move(to_move, anchor=None, direction=None, model_name=None, all_the_way=False):
    if isinstance(to_move, int) and model_name is not None:
        to_move = _instance_from_dict({'id': to_move, 'type': model_name})
    else:
        to_move = _instance_from_dict(to_move)

    model_class = to_move.__class__

    final_sink = False
    # Handle all_the_way
    if all_the_way:
        if direction == 'float':
            fake_model_dict = {
                'id': DBSession.query(
                    model_class.id,
                    model_class.display_position
                ) \
                .order_by(model_class.display_position) \
                .filter_by(state=u'active').all()[0][0],
                'type': model_class.__name__,
            }
            anchor = _instance_from_dict(fake_model_dict)
        elif direction == 'sink':
            fake_model_dict = {
                'id': DBSession.query(
                    model_class.id,
                    model_class.display_position
                ) \
                .order_by(model_class.display_position) \
                .filter_by(state=u'active').all()[-1][0],
                'type': model_class.__name__,
            }
            anchor = _instance_from_dict(fake_model_dict)
            final_sink = True
        else:
            raise Exception('move() with all_the_way as True must have direction of "float" or "sink".')
    else:
        if anchor is not None:
            if isinstance(anchor, int) and model_name is not None:
                anchor = _instance_from_dict({'id': anchor, 'type': model_name})
            else:
                anchor = _instance_from_dict(anchor)
            if model_class != anchor.__class__:
                raise Exception('move() with an anchor must receive model dictionaries with types that match.')

    if not hasattr(model_class, 'display_position'):
        raise Exception('move() must be called on a model with a display_position.')

    results = None
    if anchor is not None:
        and_clause = None
        if to_move.display_position > anchor.display_position: # float
            direction = 'float'
            and_clause = and_(
                model_class.display_position <= to_move.display_position,
                model_class.display_position >= anchor.display_position,
            )
        elif to_move.display_position < anchor.display_position: # sink
            direction = 'sink'
            and_clause = and_(
                model_class.display_position >= to_move.display_position,
                model_class.display_position <= anchor.display_position,
            )
        query = DBSession.query(model_class).filter(and_clause)
        query = query.filter_by(state=u'active').order_by(model_class.display_position)
        results = query.all()

    elif direction == 'float' or direction == 'sink':
        display_positions = [result[0] for result in DBSession.query(model_class.display_position).order_by(model_class.display_position).filter_by(state=u'active').all()]
        idx = display_positions.index(to_move.display_position)
        or_clause = None
        if direction == 'float':
            if idx == 0:
                return
            or_clause = or_(
                model_class.display_position == to_move.display_position,
                model_class.display_position == display_positions[idx - 1],
            )
        if direction == 'sink':
            if idx < len(display_positions) - 2: # If it's not the last or next to last
                or_clause = or_(
                    model_class.display_position == to_move.display_position,
                    model_class.display_position == display_positions[idx + 1],
                    model_class.display_position == display_positions[idx + 2], # Need this extra one because the logic below gets us *above* the last element in results
                )
            elif idx == len(display_positions) - 2:
                or_clause = or_(
                    model_class.display_position == to_move.display_position,
                    model_class.display_position == display_positions[idx + 1],
                )
                final_sink = True
        query = DBSession.query(model_class).filter(or_clause).order_by(model_class.display_position)
        results = query.all()

    else:
        raise Exception('move() called without an anchor must be provided "float" or "sink" as direction.')

    # This whole thing is ugly because of the necessity of multiple commits.  I apologize to the world.  If you ignore the multiple commits, I think it doesn't look so bad.
    if direction == 'float': # to_move is at the heavy end of display_position. So all the others sink, and to_move goes at the lightest end.
        moving_to = results[0].display_position
        for i in xrange(len(results) - 1):
            new_display_position_for_i = results[i + 1].display_position
            old_display_position_for_i = results[i].display_position
            results[i + 1].display_position = -1
            DBSession.flush()
            results[i].display_position = new_display_position_for_i
            DBSession.flush()
            results[i + 1].display_position = old_display_position_for_i
            DBSession.flush()
        results[-1].display_position = moving_to
    elif direction == 'sink': # to_move is at the light end of display_position. So all the others except the last one float, and to_move goes at one lighter than the heaviest end.
        if len(results) > 2:
            moving_to = results[-2].display_position
            for i in xrange(len(results) - 2, 0, -1):
                new_display_position_for_i = results[i - 1].display_position
                old_display_position_for_i = results[i].display_position
                results[i - 1].display_position = -1
                DBSession.flush()
                results[i].display_position = new_display_position_for_i
                DBSession.flush()
                results[i - 1].display_position = old_display_position_for_i
                DBSession.flush()
            results[0].display_position = moving_to
        if final_sink:
            display_position_start = results[0].display_position
            display_position_end = results[-1].display_position
            results[0].display_position = -1
            DBSession.flush()
            results[-1].display_position = display_position_start
            DBSession.flush()
            results[0].display_position = display_position_end
    else:
        raise Exception('move() must be called with direction of "float", "sink", or None.')

# End stuff for moving

# Start stuff for searching

def search(search_string, only=None, exclude=None):
    to_return = {}
    objects = ('Todo', 'Project', 'Tag', 'Note')
    if only is not None:
        objects = only
    if exclude is not None:
        objects = set(objects)
        for o in exclude:
            objects.remove(o)
    for o in objects:
        primary_descriptor = eval(o).primary_descriptor()
        to_return[o] = [result.to_dict() for result in DBSession.query(eval(o)).filter(eval('{0}.{1}'.format(o, primary_descriptor)).like(u'%{0}%'.format(search_string))).all()]
    return to_return

# End stuff for searching
