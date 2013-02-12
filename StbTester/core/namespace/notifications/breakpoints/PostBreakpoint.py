'''
Created on 22 Nov 2012

@author: francis
'''

class PostBreakpoint(object):
    def __init__(self, timeEnd, result, isErr):
        self._timeEnd = timeEnd
        self._result = result
        self._isErr = isErr
    def timeEnd(self):
        return self._timeEnd
    def result(self):
        return self._result
    def isErr(self):
        return self._isErr
