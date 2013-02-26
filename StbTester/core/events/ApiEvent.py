'''
Created on 9 Nov 2012

@author: francis
'''

from StbTester.core.events.Event import Event

class ApiEvent(Event):
    PREFIX = "API-CALL-COMPLETE"
    def __str__(self):
        result = "%(T)s ApiEvent: %(API)s( %(A)s, %(K)s )"%{"API":self.api(), "T":self.timestamp(), "A":self.args(), "K":self.kwargs()}
        return result
    def api(self):
        try:
            return self._args[1]
        except Exception, _e:
            return "None"
    def args(self):
        try:
            return self._args[2:]
        except Exception, _e:
            return "None"

