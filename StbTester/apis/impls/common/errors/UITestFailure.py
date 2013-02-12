'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.core.errors.UiError import UiError

class UITestFailure(UiError):
    def __init__(self, screenshot):
        self._screenshot = screenshot
    def screenshot(self):
        return self._screenshot
