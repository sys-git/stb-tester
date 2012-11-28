'''
Created on 9 Nov 2012

@author: francis
'''

from StbTester.core.events.Event import Event

class ApiEvent(Event):
    PREFIX = "API-CALL-COMPLETE"
    def __str__(self):
        result = "%(T)s ApiEvent: %(N)s( %(A)s, %(K)s )"%{"N":self.api(), "T":self.timestamp(), "A":self.args(), "K":self.kwargs()}
        return result
    def api(self):
        return self._args[0]
    def args(self):
        return self._args[1:]

