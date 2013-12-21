from sqlalchemy.inspection import inspect

from pydiditbackend.models import Base

class Model(object):
    '''Model object'''

    def to_dict(self, follow_relationships=True):
        to_return = {}
        for column in inspect(self.__class__).mapper.columns:
            to_return[column.name] = getattr(self, column.name)
        relationship_names = []
        if follow_relationships and isinstance(self, Base):
            relationship_names.extend([relationship_name for relationship_name in inspect(self.__class__).mapper.relationships.keys()])

        to_return['type'] = self.__class__.__name__
        to_return['primary_descriptor'] = self.get_primary_descriptor()

        for attr in relationship_names: # Will only run if follow_relationships is True; see above
            value = getattr(self, attr)
            if hasattr(value, 'to_dict'):
                to_return[attr] = value.to_dict(follow_relationships = False)
            elif hasattr(value, '__iter__'):
                new_list = []
                for element in value:
                    if hasattr(element, 'to_dict'):
                        new_list.append(element.to_dict(follow_relationships = False))
                    else:
                        new_list.append(element)
                to_return[attr] = new_list

        return to_return
