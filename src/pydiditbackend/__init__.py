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

from models.User import User

from models.Workspace import Workspace
from models.WorkspacePermission import WorkspacePermission

from models import Base

DBSession = None

import logging
log = logging.getLogger(__name__)

def initialize(ini_filenames=(os.path.expanduser('~/.pydiditrc'),
                              os.path.expanduser('~/.pydidit-backendrc')),
               external_config_fp=None,
               session_override=None):
    # Allows for the front end to define its own session scope
    global DBSession
    if session_override is None:
        DBSession = scoped_session(sessionmaker())
        register(DBSession, keep_session=True)
    else:
        DBSession = session_override

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

# Right now, an object will never tell you about its workspace(s).  You can
# though, get a workspace back in a model_dict if you just made the object.
def get(user_id, workspace_id, model_name, all=False, filter_by=None):
    # TODO: validate model_name to avoid eval() injection

    # DEPRECATED COMMENT
    # Because we need to allow access for an existing Workspace permission
    # and for an existing object-specific permission, we can't just inner
    # join both types of permissions.  We'd have to outer join then do
    # work in the application to determine access, which means we could be
    # bringing in *every* object (say, Todos!) each time.  I'm choosing now
    # to instead rely on multiple queries: one via WorkspacePermission and
    # one via the object's Permission, which will join in the object's info.

    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_read(user_id):
        return []

    #workspace_permission_query = \
        #DBSession.query(WorkspacePermission) \
                 #.filter_by(user_id=user_id) \
                 #.filter_by(workspace_id=workspace_id)

    #object_permission_query =
        #DBSession.query(eval('{0}Permission'.format(model_name)))
                 #.filter_by(user_id=user_id)
                 #.filter_by(workspace_id=workspace_id)

    query = getattr(workspace, relationship_name('Workspace', model_name))

    if filter_by is not None:
        query = query.filter_by(**filter_by)
    else:
        if hasattr(eval(model_name), 'state') and not all:
            query = query.filter_by(state=u'active')
    if hasattr(eval(model_name), 'display_position'):
        query = query.order_by(eval(model_name).display_position)
    results = query.all()
    return [obj.to_dict() for obj in results]


def get_like(user_id, workspace_id, model_dict, all=False, filter_by=None):
    return get(user_id, workspace_id, str(model_dict['type']), all, filter_by)

# End stuff for reading

# Start stuff for creating

def get_new_lowest_display_position(model_name):
    display_positions = \
        [result[0] for result in DBSession.query(eval(model_name).display_position).order_by(eval(model_name).display_position).all()]
    return 0 if not display_positions else int(display_positions[-1]) + 1


def make(user_id, workspace_id, model_name, description_text_name, display_position=None):
    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_write(user_id):
        return []

    return_single = False
    if isinstance(description_text_name, basestring):
        description_text_name = [description_text_name]
        return_single = True

    new_instances = []
    new_dicts = []
    if model_name == 'Todo' or model_name == 'Project':
        # Todo/Project.create() has some internal looping capability, but I'm
        # not using it here.
        for description in description_text_name:
            new_todo_or_project = eval(model_name).create(
                description, get_new_lowest_display_position(model_name)
            )[0]
            new_todo_or_project.workspaces.append(workspace)
            DBSession.add(new_todo_or_project)
            new_instances.append(new_todo_or_project)
            new_dicts.append(new_todo_or_project.to_dict())
    elif model_name == 'Note' or model_name == 'Tag':
        # Note.create() has some internal looping capability, but I'm
        # not using it here.
        for text_or_name in description_text_name:
            new_note_or_tag = eval(model_name).create(text_or_name)[0]
            new_note_or_tag.workspaces.append(workspace)
            DBSession.add(new_note_or_tag)
            new_instances.append(new_note_or_tag)
            new_dicts.append(new_note_or_tag.to_dict())
    flush()
    for i in xrange(len(new_instances)):
        new_dicts[i]['id'] = new_instances[i].id

    return new_dicts[0] if return_single else new_dicts


def make_like(user_id, workspace_id, model_dict, description_text_name, display_position=None):
    return make(user_id, workspace_id, model_dict['type'], description_text_name, display_position)

# Backward compatibility
put = make

def put_like(user_id, workspace_id, model_dict, description_text_name):
    return put(user_id, workspace_id, str(model_dict['type']), description_text_name)

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

# TODO: note that right now, users are globally discoverable
def get_users(username=None):
    query = DBSession.query(User)
    if username is not None:
        query = query.filter_by(username=username)
    return [{'username': user.username, 'user_id': user.id} for user in query.all()]

def create_user(usernames):
    # Because we assume that a front-end has direct DB access, we are ok with
    # allowing an anonymous create_user() call.  The pyramid gateway will
    # impose some auth on top on this.
    if isinstance(usernames, basestring):
        usernames = (usernames,)

    new_users = []
    new_user_dicts = []
    for username in usernames:
        new_user = User(username)
        DBSession.add(new_user)

        # Assigns user id so we can call create_workspace()
        DBSession.flush()

        new_workspace_dict = create_workspace(
            new_user.id,
            username,
            'Default workspace for {0}'.format(username)
        )[0]

        new_user_dicts = new_user.to_dict()
    return new_user_dicts

# TODO: note that right now, workspaces are globally discoverable
def get_workspaces(user_id, workspace_name=None):
    query = DBSession.query(Workspace)
    if workspace_name is not None:
        query = query.filter_by(name=workspace_name)
    return [{'name': workspace.name, 'workspace_id': workspace.id} for workspace in query.all() if workspace.can_read(user_id)]

def create_workspace(user_id, names, descriptions):
    if isinstance(names, basestring) and isinstance(descriptions, basestring):
        names = (names,)
        descriptions = (descriptions,)

    if len(names) != len(descriptions):
        raise Exception('Must pass same number of Workspace names and descriptions.')

    new_workspace_dicts = []
    for name, description in zip(names, descriptions):
        new_workspace = Workspace(name, description)
        DBSession.add(new_workspace)

        # Get a workspace id
        DBSession.flush()

        workspace_permission = give_permission(
            user_id,
            new_workspace.id,
            user_id,
            ('read', 'write', 'delete')
        )

        new_workspace_dicts.append(new_workspace.to_dict())

    return new_workspace_dicts

def give_permission(user_id, workspace_id, target_user_id, permissions):
    # For now, only allow users with write on a workspace to change
    # permissions on that workspace.
    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_write(user_id):
        return None

    allowed_permissions = ('read', 'write', 'delete')
    if isinstance(permissions, basestring):
        permissions = (permissions,)

    # Do we already have a permission record for this user/workspace?
    workspace_permission = \
        DBSession.query(WorkspacePermission) \
                 .filter_by(workspace_id=workspace_id) \
                 .filter_by(user_id=target_user_id).all()

    if len(workspace_permission) == 0:
        workspace_permission = WorkspacePermission(
            user_id=target_user_id,
            workspace_id=workspace_id
        )
        workspace_permission.workspace = workspace
        DBSession.add(workspace_permission)
    elif len(workspace_permission) == 1:
        workspace_permission = workspace_permission[0]
    # len > 1 is forbidden by primary key on database

    for permission in permissions:
        if permission in allowed_permissions:
            setattr(workspace_permission, permission, True)

    return workspace_permission

def revoke_permission(user_id, workspace_id, target_user_id, permissions):
    # For now, only allow users with write on a workspace to change
    # permissions on that workspace.
    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_write(user_id):
        return []

    allowed_permissions = ('read', 'write', 'delete')
    if isinstance(permissions, basestring):
        permissions = (permissions,)

    workspace_permission = \
        DBSession.query(WorkspacePermission) \
                 .filter_by(workspace_id=workspace_id) \
                 .filter_by(user_id=target_user_id).all()

    if len(workspace_permission) == 1:
        workspace_permission = workspace_permission[0]

        for permission in permissions:
            if permission in allowed_permissions:
                # Never let a user revoke his/her own write permission, to avoid someone
                # getting locked out of a workwpace entirely.
                if not (user_id == target_user_id and permission == 'write'):
                    setattr(workspace_permission, permission, False)
    # len > 1 is forbidden by primary key on database

# End utilities

# Start stuff for deleting

def delete_from_db(user_id, workspace_id, model_dict):
    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_delete(user_id):
        return []

    DBSession.delete(_instance_from_dict(model_dict))
    return model_dict

# End stuff for deleting

# Start stuff for updating

def set_completed(user_id, workspace_id, model_dict):
    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_write(user_id):
        return None

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

def set_attributes(user_id, workspace_id, model_dict, new_values):
    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_write(user_id):
        return None

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

def link(user_id, workspace_id, parent_dict, child_dict, *args, **kwargs):
    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_write(user_id):
        return None

    # TODO: When I add in per-record permissions, I think I want write on
    # both parent and child to allow linking.

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

def unlink(user_id, workspace_id, parent_dict, child_dict, *args, **kwargs):
    # Permissions enforced in link()

    kwargs['unlink'] = True
    return link(user_id, workspace_id, parent_dict, child_dict, *args, **kwargs)

# End stuff for relationships

# Start stuff for moving

def move(user_id, workspace_id, to_move, anchor=None, direction=None, model_name=None, all_the_way=False):
    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_write(user_id):
        return None

    # TODO: how will this handle side effects and permission?  that is, if I know i can
    # write to the object to_move, but i don't know if I can write to any of the objects
    # that will get shuffled to accommodate the movement.
    # My gut right now says that moving should only be allowed if all of the side affected 
    # objects are also writable (or in the same workspace?)
    # Or is it that, even if display_position is not specific to a workspace but is global,
    # no movement in one workspace will effect the display in another?  I think this is true.
    # This means that it's ok to not check intervening objects for now, but when we do
    # permissions on specific objects within workspaces, we will likely have to TODO revisit this.
    # So note that the constraint on display_position is global and NOT workspace specific!
    # We're leaving it this way for now.

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

    return to_move.display_position

# End stuff for moving

# Start stuff for searching

def search(user_id, workspace_id, search_string, only=None, exclude=None):
    to_return = {}

    workspace = DBSession.query(Workspace).filter_by(id=workspace_id).one()
    if not workspace.can_read(user_id):
        return to_return

    objects = ('Todo', 'Project', 'Tag', 'Note')
    if only is not None:
        objects = only
    if exclude is not None:
        objects = set(objects)
        for o in exclude:
            objects.remove(o)
    for o in objects:
        query = getattr(workspace, relationship_name('Workspace', o))

        primary_descriptor = eval(o).primary_descriptor()
        to_return[o] = [result.to_dict() for result in query.filter(eval('{0}.{1}'.format(o, primary_descriptor)).like(u'%{0}%'.format(search_string))).all()]
    return to_return

# End stuff for searching
