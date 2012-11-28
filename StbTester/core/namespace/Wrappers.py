'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.namespace.breakpoints.PostApiBreakpoint import \
    PostApiBreakpoint
from StbTester.core.namespace.breakpoints.PreApiBreakpoint import \
    PreApiBreakpoint
import inspect
import time

def _wrapFuncs(ns, target, waitOnEvent=True):
    try:
        event = target._event
    except Exception, _e:
        waitOnEvent = False
        event = None
    for name, func in ns.items():
        setattr(target, name, _funcWrapper(target, name, func, event, waitOnEvent=waitOnEvent))

def _funcWrapper(target, name, func, event, waitOnEvent=None):
    try:
        checkAborted = func.im_self.checkAborted
    except Exception, _e:
        checkAborted = lambda: None
    def _functionWrapper(*args, **kwargs):
        #    Inspect the call-stack and emit (module, line) so we can highlight in the editor.
        callers = inspect.stack()
        frame = callers[1]
#        callersFrame = frame[0]
#        callersName = frame[3]
#        callersDoc = callersFrame.f_globals[callersName].func_doc
        filename = frame[1]
        lineNumber = frame[2]
        checkAborted()
        try:
            print "API called: %(N)s"%{"N":name}
            timeStart = time.time()
            if event!=None:
                (eventNotifierEntry, eventNotifierContinue, eventWaiter, ignore) = event
            def handle(result, filename, lineNumber, isErr=False):
                checkAborted()
                timeEnd = time.time()
                if waitOnEvent!=None:   #    UI ?
                    if event!=None:
                        needToWait = waitOnEvent()
                        if (needToWait==True):  #    Stepping?
                            #    Notify that we are about to wait:
                            eventNotifierEntry.set(PostApiBreakpoint(name, args, kwargs, timeStart, callers[1:], filename, lineNumber, timeEnd, result, isErr))
                            checkAborted()
                            eventNotifierContinue.wait()
                            checkAborted()
                            if isErr==False:
                                #    Now wait for permission to continue (UI to 'step'):
                                eventWaiter.wait()
                                #    Now-reset it:
                                eventWaiter.clear()
                                #    We should now wait next time.
                        else:
                            eventNotifierEntry.set(PostApiBreakpoint(name, args, kwargs, timeStart, callers[1:], filename, lineNumber, timeEnd, result, isErr))
                            checkAborted()
                            eventNotifierContinue.wait()
                            checkAborted()
            #    Allow wait prior to api execution, inform: (filename, lineNumber) to allow UI to update.
            if waitOnEvent!=None:   #    UI?
                if event!=None:
                    needToWait = waitOnEvent()
                    if needToWait:
                        eventNotifierEntry.set(PreApiBreakpoint(name, args, kwargs, timeStart, callers[1:], filename, lineNumber))
                        checkAborted()
                        eventNotifierContinue.wait()
                        checkAborted()
                        #    Now wait for permission to continue (UI to 'step'):
                        eventWaiter.wait()
                        #    Now-reset it:
                        eventWaiter.clear()
            try:
                result = func(*args, **kwargs)
            except Exception, result:
                if ignore.isSet()==False:
                    handle(result, filename, lineNumber, isErr=True)
                raise
            if ignore.isSet()==False:
                handle(result, filename, lineNumber, isErr=False)
            return result
        finally:
            checkAborted()
    return _functionWrapper
