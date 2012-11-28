'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.namespace.breakpoints.BaseBreakpoint import BaseBreakpoint

class PostApiBreakpoint(BaseBreakpoint):
    def __init__(self, name, args, kwargs, timeStart, callersStack, filename, lineNumber, timeEnd, result, isErr):
        super(PostApiBreakpoint, self).__init__(name, args, kwargs, timeStart, callersStack, filename, lineNumber, isErr=isErr)
        self._timeEnd = timeEnd
        self._result = result
    def timeEnd(self):
        return self._timeEnd
    def result(self):
        return self._result
