'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.namespace.notifications.breakpoints.BaseBreakpoint import \
    BaseBreakpoint
from StbTester.core.namespace.notifications.breakpoints.CallBreakpoint import \
    CallBreakpoint
from StbTester.core.namespace.notifications.breakpoints.PreBreakpoint import PreBreakpoint

class PreApiCallBreakpoint(BaseBreakpoint, CallBreakpoint, PreBreakpoint):
    def __init__(self, name, apid, args, kwargs, timeStart, frames, filename, lineNumber):
        BaseBreakpoint.__init__(self, timeStart, frames, filename, lineNumber)
        CallBreakpoint.__init__(self, name, apid, args, kwargs)
        PreBreakpoint.__init__(self)
