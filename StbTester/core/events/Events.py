'''
Created on 9 Nov 2012

@author: francis
'''

from StbTester.core.events.ApiEvent import ApiEvent
from StbTester.core.events.AppEvent import AppEvent
from StbTester.core.events.Event import Event
from StbTester.core.events.RunnerEvent import RunnerEvent
from multiprocessing.synchronize import Lock
import sys

class Events(object):
    def __init__(self):
        self._events = []
        self._lock = Lock()
    def __call__(self, *args, **kwargs):
        name = args[0]
        with self._lock:
            if name==ApiEvent.PREFIX:
                evt = ApiEvent
            elif name.startswith(RunnerEvent.PREFIX):
                evt = RunnerEvent
            elif name.startswith(AppEvent.PREFIX):
                evt = AppEvent
            else:
                evt = Event
            self._events.append(evt(*args, **kwargs))
    def dump(self, writer=None):
        if writer==None:
            writer = sys.stderr
        with self._lock:
            s = ["Event dump..."]
            for event in self._events:
                s.append(str(event))
        ss = "\n".join(s)
        writer.write("\n"+ss+"\n")
        return ss
    def __str__(self):
        return "Events: %(N)s"%{"N":len(self._events)}
