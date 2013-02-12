'''
Created on 2 Nov 2012

@author: YouView
'''

from StbTester.core.errors.MaskedAttributeError import MaskedAttributeError
from StbTester.core.namespace.Wrappers import _wrapFuncs

class NamespaceWrapper(object):
    def __init__(self, apid, ns, waitOnEvent=True, event=None, debugger=None):
        self._ns = ns
        self._apid = apid
        self._waitOnEvent = waitOnEvent
        self._debugger = debugger
        eNames = dir(self)
        for name in ns.keys():
            if name in eNames:
                raise MaskedAttributeError(name)
        _wrapFuncs(ns, apid, self, waitOnEvent=self._waitOnEvent, event=event, debugger=debugger)
    def namespace(self):
        return self._ns
