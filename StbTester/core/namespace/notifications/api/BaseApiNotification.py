'''
Created on 5 Dec 2012

@author: francis
'''

from StbTester.core.namespace.notifications.BaseNotification import \
    BaseNotification

class BaseApiNotification(BaseNotification):
    def __init__(self, scriptName, timeStart, apid, result, callersStack, filename, lineNumber):
        super(BaseApiNotification, self).__init__(timeStart, callersStack, filename, lineNumber)
        self._scriptName = scriptName
        self._apid = apid
        self._result = result
    def scriptName(self):
        return self._scriptName
    def apid(self):
        return self._apid
    def result(self):
        return self._result
    def isErr(self):
        return isinstance(self._result, Exception)

