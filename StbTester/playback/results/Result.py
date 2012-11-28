'''
Created on 8 Nov 2012

@author: francis
'''

from StbTester.playback.results.BaseResult import BaseResult

class Result(BaseResult):
    OK = "no exception"
    def __init__(self, result):
        super(Result, self).__init__()
        self._result = result
    def result(self):
        return self._result
    def __str__(self):
        return "Result: %(T)s( %(R)s )"%{"T": type(self._result), "R":self._result}
