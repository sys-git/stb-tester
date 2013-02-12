'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.namespace.notifications.breakpoints.BaseBreakpoint import \
    BaseBreakpoint
from StbTester.core.namespace.notifications.breakpoints.CallBreakpoint import \
    CallBreakpoint
from StbTester.core.namespace.notifications.breakpoints.PostBreakpoint import \
    PostBreakpoint

class PostApiCallBreakpoint(BaseBreakpoint, CallBreakpoint, PostBreakpoint):
    def __init__(self, name, apid, args, kwargs, timeStart, frames, filename, lineNumber, timeEnd, result, isErr=False):
        BaseBreakpoint.__init__(self, timeStart, frames, filename, lineNumber)
        CallBreakpoint.__init__(self, name, apid, args, kwargs)
        PostBreakpoint.__init__(self, timeEnd, result, isErr)
