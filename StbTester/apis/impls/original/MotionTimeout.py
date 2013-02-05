'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.apis.impls.common.errors.UITestFailure import UITestFailure

class MotionTimeout(UITestFailure):
    def __init__(self, screenshot, mask, timeoutSecs):
        self._screenshot = screenshot
        self._mask = mask
        self._timeoutSecs = timeoutSecs
    def screenshot(self):
        return self._screenshot
    def timeoutSecs(self):
        return self._timeoutSecs
    def mask(self):
        return self._mask
    def __str__(self):
        return ",".join(["MotionTimeout",
                         "timeout: %(T)s"%{"T":self._timeoutSecs},
                         "mask: %(E)s"%{"E":self._mask},
                         "screenshot: %(F)s"%{"F":self._screenshot!=None},
                         ])
