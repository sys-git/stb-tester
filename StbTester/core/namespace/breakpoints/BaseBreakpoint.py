'''
Created on 22 Nov 2012

@author: francis
'''

class BaseBreakpoint(object):
    def __init__(self, name, args, kwargs, timeStart, callersStack, filename, lineNumber, isErr=False):
        self._name = name
        self._args = args
        self._kwargs = kwargs
        self._timeStart = timeStart
        self._callersStack = callersStack
        self._filename = filename
        self._lineNumber = lineNumber
        self._isErr = isErr
    def name(self):
        return self._name
    def args(self):
        return self._args
    def kwargs(self):
        return self._kwargs
    def timeStart(self):
        return self._timeStart
    def callersStack(self):
        return self._callersStack
    def filename(self):
        return self._filename
    def lineNumber(self):
        return self._lineNumber
    def isErr(self):
        return self._isErr
