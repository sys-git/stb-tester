'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.debugging.BreakpointStepper import BreakpointStepper
from StbTester.core.namespace.notifications.breakpoints.PostApiCallBreakpoint import \
    PostApiCallBreakpoint
from StbTester.core.namespace.notifications.breakpoints.PreApiCallBreakpoint import \
    PreApiCallBreakpoint
import inspect

def _wrapFuncs(ns, apid, target, waitOnEvent=True, event=None, debugger=None):
    if event==None:
        waitOnEvent = False
    for name, func in ns.items():
        setattr(target, name, _funcWrapper(target, name, func, event, apid, waitOnEvent=waitOnEvent, debugger=debugger))

def _funcWrapper(target, name, func, event, apid, waitOnEvent=None, debugger=None):
    try:
        checkAborted = func.im_self.checkAborted
    except Exception, _e:
        checkAborted = lambda: None
    def _functionWrapper(*args, **kwargs):
        #    Inspect the call-stack and emit (module, line) so we can highlight in the editor.
        callers = inspect.stack()
        def getPreNotifier(timeStart, frames, filename, lineNumber):
            return PreApiCallBreakpoint(name, apid, args, kwargs, timeStart, frames, filename, lineNumber)
        def getPostNotifier(timeStart, frames, filename, lineNumber, timeEnd, result, isErr):
            return PostApiCallBreakpoint(name, apid, args, kwargs, timeStart, frames, filename, lineNumber, timeEnd, result, isErr)
        return BreakpointStepper(  event,
                                   checkAborted,
                                   debugger,
                                   "API called: %(API)s.%(N)s"%{"N":name, "API":apid.ns()},
                                   lambda: func(*args, **kwargs),
                                   callers[1:],
                                   getPreNotifier,
                                   getPostNotifier,
                                   waitOnEvent=waitOnEvent,
                                   )
    return _functionWrapper
