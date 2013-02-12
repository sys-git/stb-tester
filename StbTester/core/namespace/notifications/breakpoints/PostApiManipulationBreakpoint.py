'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.namespace.notifications.breakpoints.BaseBreakpoint import \
    BaseBreakpoint
from StbTester.core.namespace.notifications.breakpoints.ManipulationBreakpoint import \
    ManipulationBreakpoint
from StbTester.core.namespace.notifications.breakpoints.PostBreakpoint import \
    PostBreakpoint

class PostApiManipulationBreakpoint(BaseBreakpoint, ManipulationBreakpoint, PostBreakpoint):
    def __init__(self, whats, mode, timeStart, frames, filename, lineNumber, timeEnd, result, isErr=False):
        BaseBreakpoint.__init__(self, timeStart, frames, filename, lineNumber)
        ManipulationBreakpoint.__init__(self, whats, mode)
        PostBreakpoint.__init__(self, timeEnd, result, isErr)
