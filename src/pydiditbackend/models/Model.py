class Model(object):
    '''Model object'''

    def to_dict(self):
        to_return = self.__dict__
        del to_return['_sa_instance_state']
        for attr, value in to_return.iteritems():
            if hasattr(value, 'to_dict'):
                to_return[attr] = value.to_dict()
            elif hasattr(value, '__iter__'):
                to_return[attr] = [element.to_dict() for element in value]
        to_return['type'] = self.__class__.__name__
        return to_return
