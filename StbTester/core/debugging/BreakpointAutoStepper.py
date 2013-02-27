'''
Created on 27 Feb 2013

@author: francis
'''

import threading

class AutoStepper(object):
    def __init__(self, canStop=lambda: False):
        self.event = None
        self.canStop = canStop
    def func(self, event):
        self.event = event
        (eventNotifierEntry, eventNotifierContinue) = event
        def run():
            while self.canStop()==False:
                eventNotifierEntry.wait()
                eventNotifierEntry.clear()
                eventNotifierContinue.set()
        threading.Thread(target=run).start()
    def kill(self):
        try:
            (eventNotifierEntry, eventNotifierContinue) = self.event
        except Exception, _e:
            pass
        else:
            eventNotifierEntry.set()
            eventNotifierContinue.set()
