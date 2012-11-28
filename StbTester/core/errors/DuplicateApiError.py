'''
Created on 6 Nov 2012

@author: francis
'''

from StbTester.core.errors.ConfigurationError import ConfigurationError

class DuplicateApiError(ConfigurationError):
    def __init__(self, names):
        self._names = names
        super(DuplicateApiError, self).__init__(names)
    def names(self):
        return self._names
