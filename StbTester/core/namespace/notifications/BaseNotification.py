'''
Created on 5 Dec 2012

@author: francis
'''

class BaseNotification(object):
    def __init__(self, timeStart, callersStack, filename, lineNumber):
        self._timeStart = timeStart
        self._callersStack = callersStack
        self._filename = filename
        self._lineNumber = lineNumber
    def timeStart(self):
        return self._timeStart
    def callersStack(self):
        return self._callersStack
    def filename(self):
        return self._filename
    def lineNumber(self):
        return self._lineNumber

