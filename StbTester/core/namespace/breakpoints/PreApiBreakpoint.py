'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.namespace.breakpoints.BaseBreakpoint import BaseBreakpoint

class PreApiBreakpoint(BaseBreakpoint):
    def __init__(self, name, args, kwargs, timeStart, callersStack, filename, lineNumber):
        super(PreApiBreakpoint, self).__init__(name, args, kwargs, timeStart, callersStack, filename, lineNumber)
