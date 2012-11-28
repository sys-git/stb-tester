'''
Created on 2 Nov 2012

@author: YouView
'''

from StbTester.core.errors.MaskedAttributeError import MaskedAttributeError
from StbTester.core.namespace.Wrappers import _wrapFuncs
from StbTester.core.utils.DataEvent import DataEvent

class NamespaceWrapper(object):
    _event = (DataEvent(), DataEvent(), DataEvent(), DataEvent())
    def __init__(self, ns, waitOnEvent=True):
        self._ns = ns
        self._waitOnEvent = waitOnEvent
        eNames = dir(self)
        for name in ns.keys():
            if name in eNames:
                raise MaskedAttributeError(name)
        _wrapFuncs(ns, self, waitOnEvent=self._waitOnEvent)
    @staticmethod
    def ignoreEvents(enabler=False):
        (_, _, _, d) = NamespaceWrapper._event
        if enabler==True:
            d.set()
        else:
            d.clear()
