'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.namespace.notifications.breakpoints.BaseBreakpoint import \
    BaseBreakpoint
from StbTester.core.namespace.notifications.breakpoints.ManipulationBreakpoint import \
    ManipulationBreakpoint
from StbTester.core.namespace.notifications.breakpoints.PreBreakpoint import \
    PreBreakpoint

class PreApiManipulationBreakpoint(BaseBreakpoint, ManipulationBreakpoint, PreBreakpoint):
    def __init__(self, whats, mode, timeStart, frames, filename, lineNumber):
        BaseBreakpoint.__init__(self, timeStart, frames, filename, lineNumber)
        ManipulationBreakpoint.__init__(self, whats, mode)
        PreBreakpoint.__init__(self)
