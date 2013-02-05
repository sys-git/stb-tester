'''
Created on 2 Nov 2012

@author: YouView
'''

class UiError(Exception):
    r"""
    @summary: The superclass error for all StbTester exceptions raised, this
    includes the API and Core.
    """
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self._scriptName = None
        self._resultName = None
    def setScriptName(self, name):
        self._scriptName = name
    def scriptName(self):
        return self._scriptName
    def setResultName(self, name):
        self._resultName = name
    def resultName(self):
        return self._resultName
