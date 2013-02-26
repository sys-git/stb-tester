'''
Created on 6 Nov 2012

@author: francis
'''

from threading import Event, Lock

class DataEvent(object):
    def __init__(self):
        self._event = Event()
        #    Only way to avoid race-condition data-loss.
        self._data = []
        self._lock = Lock()
    def data(self):
        with self._lock:
            result = self._data
            self._data = []
            return result
    def reset(self):
        with self._lock:
            self._data = []
    def set(self, *args):
        with self._lock:
            try:
                self._data.append(args[0])
            except Exception, _e:
                pass
        return self._event.set()
    def is_set(self, *args, **kwargs):
        return self._event.is_set(*args, **kwargs)
    def isSet(self, *args, **kwargs):
        return self._event.isSet(*args, **kwargs)
    def clear(self, *args, **kwargs):
        return self._event.clear(*args, **kwargs)
    def wait(self, *args, **kwargs):
        return self._event.wait(*args, **kwargs)
