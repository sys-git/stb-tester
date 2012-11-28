'''
Created on 2 Nov 2012

@author: YouView
'''

class BaseDisplay(object):
    def __init__(self, debugger, getWindowId):
        self._debugger = debugger
        self._getWindowId = getWindowId
        self._pipeline = None
        self._screenshot = None
    def _setPipeline(self, pipeline):
        self._pipeline = pipeline
    def getPipeline(self):
        return self._pipeline
    def getWindowId(self):
        if self._getWindowId!=None:
            return self._getWindowId()
    def _setScreenshot(self, screenshot):
        self._screenshot = screenshot
    def getScreenshot(self):
        return self._screenshot
