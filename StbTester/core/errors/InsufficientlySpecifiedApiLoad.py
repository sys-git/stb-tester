'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.core.errors.UnknownApiError import UnknownApiError

class InsufficientlySpecifiedApiLoad(UnknownApiError):
    def __init__(self, type_, matching):
        super(InsufficientlySpecifiedApiLoad, self).__init__(type_, matching)
        self.type_ = type_
        self.matching = matching
