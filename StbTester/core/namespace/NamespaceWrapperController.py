'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.errors.DuplicateApiMethodError import \
    DuplicateApiMethodError
from StbTester.core.namespace.NamespaceWrapper import NamespaceWrapper
from StbTester.core.namespace.Wrappers import _wrapFuncs
from StbTester.core.utils.DataEvent import DataEvent

class NamespaceWrapperController(object):
    r"""
    @summary: controls the NamespaceWrapper without interfering with the wrapper's
    namespace.
    """
    _event = (DataEvent(), DataEvent(), DataEvent(), DataEvent())
    def __init__(self, ns, apid, cls, wrapper, waitOnEvent=True, debugger=None):
        self._ns = ns
        self._apid = apid
        self._cls = cls
        self._wrapper = wrapper
        self._debugger = debugger
        self._waitOnEvent = waitOnEvent
    def apid(self):
        return self._apid
    def getNs(self):
        return self._ns
    def getWrapper(self):
        return self._wrapper
    @staticmethod
    def stall():
        (_, _, eventWaiter, _) = NamespaceWrapperController._event
        eventWaiter.clear()
    @staticmethod
    def run():
        (_, _, eventWaiter, _) = NamespaceWrapperController._event
        eventWaiter.set()
    @staticmethod
    def getEventNotifiers():
        (eventNotifierEntry, eventNotifierContinue, _, _) = NamespaceWrapperController._event
        return (eventNotifierEntry, eventNotifierContinue)
    def insertApi(self, api):
        eNames = dir(self._wrapper)
        names = []
        newNames = api.keys()
        for name in newNames:
            if name in eNames:
                names.append(name)
        if len(names)>0:
            raise DuplicateApiMethodError(names, eNames)
        _wrapFuncs(api, self._apid, self._wrapper, self._waitOnEvent, event=NamespaceWrapperController._event, debugger=self._debugger)
        self._wrapper.namespace().update(api)
    def overwriteApi(self, api):
        _wrapFuncs(api, self._apid, self._wrapper, self._waitOnEvent, event=NamespaceWrapperController._event, debugger=self._debugger)
        self._wrapper.namespace().update(api)
    @staticmethod
    def create(apid, ns, cls=NamespaceWrapper, waitOnEvent=True, debugger=None):
        name = apid.ns()
        wrapper = cls(apid, ns, waitOnEvent=waitOnEvent, event=NamespaceWrapperController._event, debugger=debugger)
        return NamespaceWrapperController(name, apid, cls, wrapper, waitOnEvent=waitOnEvent, debugger=debugger)
    @staticmethod
    def ignoreEvents(enabler=False):
        (_, _, _, ignore) = NamespaceWrapperController._event
        if enabler==True:
            ignore.set()
        else:
            ignore.clear()
