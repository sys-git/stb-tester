'''
Created on 6 Nov 2012

@author: francis
'''

from StbTester.core.errors.ConfigurationError import ConfigurationError

class DuplicateApiNamespaceError(ConfigurationError):
    def __init__(self, names):
        self._names = names
        super(DuplicateApiNamespaceError, self).__init__(names)
    def names(self):
        return self._names
    def __str__(self):
        return "DuplicateApiNamespaceError: '%(NS)s'"%{"NS":self._names}
