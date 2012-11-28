'''
Created on 9 Nov 2012

@author: francis
'''

from StbTester.core.events.Event import Event

class AppEvent(Event):
    PREFIX = "APP"
    def __str__(self):
        result = "%(T)s AppEvent: %(N)s"%{"N":self.action(), "T":self.timestamp()}
        return result
    def action(self):
        return self.name().split("-")[1].title()

