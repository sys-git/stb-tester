'''
Created on 7 Feb 2013

@author: francis
'''

import time

class BreakpointStepper(object):
    def __new__(self,
                event,
                checkAborted,
                debugger,
                msg,
                funcToExec,
                frames,
                preNotifier,
                postNotifier,
                waitOnEvent=None,
                ):
        if debugger==None:
            print msg
        else:
            debugger.debug(msg)
        frame = frames[0]
        filename = frame[1]
        lineNumber = frame[2]
        checkAborted()
        timeStart = time.time()
        if event!=None:
            (eventNotifierEntry, eventNotifierContinue, eventWaiter, ignore) = event
        def handle(**kwargs):   #result, isErr=False):
            checkAborted()
            timeEnd = time.time()
            if waitOnEvent!=None:   #    UI ?
                if event!=None:
                    needToWait = waitOnEvent()
                    isErr = kwargs.get("isErr", None)
                    if (needToWait==True):  #    Stepping?
                        #    Notify that we are about to wait:
                        if isErr!=None:
                            result = kwargs["result"]
                            notifier_ = postNotifier(timeStart, frames, filename, lineNumber, timeEnd, result, isErr)
                        else:
                            notifier_ = preNotifier(timeStart, frames, filename, lineNumber)
                        eventNotifierEntry.set(notifier_)
                        checkAborted()
                        eventNotifierContinue.wait()
                        checkAborted()
                        if ((isErr!=None) and (isErr==False)) or (isErr==None):
                            #    Now wait for permission to continue (UI to 'step'):
                            eventWaiter.wait()
                            #    Now-reset it:
                            eventWaiter.clear()
                            #    We should now wait next time.
                    else:
                        if isErr!=None:
                            result = kwargs["result"]
                            notifier_ = postNotifier(timeStart, frames, filename, lineNumber, timeEnd, result, isErr)
                        else:
                            notifier_ = preNotifier(timeStart, frames, filename, lineNumber)
                        eventNotifierEntry.set(notifier_)
                        checkAborted()
                        eventNotifierContinue.wait()
                        checkAborted()
        #    Now execute the desired call:
        handle()
        try:
            result = funcToExec()
        except Exception, result:
            if ignore and (ignore.isSet()==False):
                handle(result=result, isErr=True)
            raise
        if ignore and (ignore.isSet()==False):
            handle(result=result, isErr=False)
        return result

if __name__ == '__main__':
    pass