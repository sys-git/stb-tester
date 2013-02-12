'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.namespace.notifications.api.ApiLoad import ApiLoad

class ApiRequires(ApiLoad):
    def __init__(self, scriptName, timeStart, whats, apid, r, callersStack, filename, lineNumber):
        super(ApiRequires, self).__init__(scriptName, timeStart, whats, apid, r, callersStack, filename, lineNumber)
    def name(self):
        return "__requires__"
    def __str__(self):
        s = [str(self.what())]
        s.append("result:")
        s.append(str(self.result()))
        return " ".join(s)
