'''
Created on 7 Feb 2013

@author: francis
'''

from StbTester.core.namespace.notifications.breakpoints.BaseBreakpoint import \
    BaseBreakpoint

class PostStepBreakpoint(BaseBreakpoint):
    def __init__(self, whats, mode, timeStart, callersStack, filename, lineNumber, timeEnd, result, isErr=False):
        super(PostStepBreakpoint, self).__init__(whats, mode, timeStart, callersStack, filename, lineNumber, isErr=isErr)
        self._whats = whats
        self._result = result
    def timeEnd(self):
        return self._timeEnd
    def result(self):
        return self._result
