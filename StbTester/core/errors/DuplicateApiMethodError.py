'''
Created on 6 Nov 2012

@author: francis
'''

from StbTester.core.errors.ConfigurationError import ConfigurationError

class DuplicateApiMethodError(ConfigurationError):
    def __init__(self, names, existingNames):
        self._names = names
        self._existingNames = existingNames
        super(DuplicateApiMethodError, self).__init__(names, existingNames)
    def names(self):
        return self._names
    def existingNames(self):
        return self._existingNames
    def __str__(self):
        return "DuplicateApiMethodError: '%(N)s' already in: '%(EN)s'"%{"N":self._names, "EN":self._existingNames}
