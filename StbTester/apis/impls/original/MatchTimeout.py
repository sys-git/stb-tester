'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.apis.impls.common.errors.UITestFailure import UITestFailure

class MatchTimeout(UITestFailure):
    def __init__(self, screenshot, expected, timeoutSecs):
        self._screenshot = screenshot
        self._expected = expected
        self._timeoutSecs = timeoutSecs
        self._scriptName = "unknown"
    def screenshot(self):
        return self._screenshot
    def timeoutSecs(self):
        return self._timeoutSecs
    def expected(self):
        return self._expected
    def setScriptName(self, scriptName):
        self._scriptName = scriptName
    def __str__(self):
        return ",".join(["MatchTimeout",
                         "timeout: %(T)s"%{"T":self._timeoutSecs},
                         "expected: %(E)s"%{"E":self._expected},
                         "screenshot: %(F)s"%{"F":self._screenshot},
                         "scriptName: %(F)s"%{"F":self._scriptName},
                         ])
