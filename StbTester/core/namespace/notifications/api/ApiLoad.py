'''
Created on 22 Nov 2012

@author: francis
'''

from StbTester.core.namespace.notifications.api.BaseApiNotification import \
    BaseApiNotification

class ApiLoad(BaseApiNotification):
    def __init__(self, scriptName, timeStart, what, apid, result, callersStack, filename, lineNumber, mode=-2):
        super(ApiLoad, self).__init__(scriptName, timeStart, apid, result, callersStack, filename, lineNumber)
        self._what = what
        self._mode = mode
    def mode(self):
        return self._mode
    def what(self):
        return self._what
    def name(self):
        return "__loads__"
    def __str__(self):
        s = [str(self.what())]
        s.append("result:")
        s.append(str(self.result()))
        return " ".join(s)
