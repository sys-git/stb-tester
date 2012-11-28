'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.errors.DuplicateApiError import DuplicateApiError
from StbTester.core.namespace.NamespaceWrapper import NamespaceWrapper
from StbTester.core.namespace.Wrappers import _wrapFuncs

class NamespaceWrapperController(object):
    r"""
    @summary: controls the NamespaceWrapper without interfering with the wrapper's
    namespace.
    """
    def __init__(self, cls, wrapper, waitOnEvent=True):
        self._cls = cls
        self._wrapper = wrapper
        self._waitOnEvent = waitOnEvent
    def getWrapper(self):
        return self._wrapper
    def stall(self):
        (_eventNotifierEntry, _eventNotifierContinue, eventWaiter, _ignore) = self._cls._event
        eventWaiter.clear()
    def run(self):
        (_eventNotifierEntry, _eventNotifierContinue, eventWaiter, _ignore) = self._cls._event
        eventWaiter.set()
    def getEventNotifiers(self):
        (eventNotifierEntry, eventNotifierContinue, _eventWaiter, _ignore) = self._cls._event
        return (eventNotifierEntry, eventNotifierContinue)
    def insertApi(self, api):
        eNames = dir(self._wrapper)
        names = []
        newNames = api.keys()
        for name in newNames:
            if name in eNames:
                names.append(name)
        if len(names)>0:
            raise DuplicateApiError(names)
        _wrapFuncs(api, self._wrapper, self._waitOnEvent)
    @staticmethod
    def create(ns, cls=NamespaceWrapper, waitOnEvent=True):
        result = NamespaceWrapperController(cls, cls(ns, waitOnEvent=waitOnEvent), waitOnEvent=waitOnEvent)
        return result
