'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.apis.impls.common.errors.AbortedException import AbortedException
import time

class BaseApi(object):
    r"""
    @attention: APIs have the following requirements.
    All public methods:
        1.    Do not begin with an underscore.
        2.    Do not begin with an upper-case character.
        3.    Do not include the method: 'namespace'.
        4.    Are case-sensitive.
        5.    Should raise ScriptApiParamError to indicate an argument is incorrect.
    """
    RESERVED_METHODS = ["namespace", "checkAborted", "abort"]
    def __init__(self, control, display, srcPath, debugger):
        self._control = control
        self._display = display
        self._srcPath = srcPath
        self._debugger = debugger
        self._aborted = False
        self._namespace = self._exportNamespace()
    def _exportNamespace(self):
        namespace = {}
        a = dir(self)
        for name in a:
            #    All script namespace items begin with non-underscore, lower-case alpha-characters!
            if (not name.startswith("_")) and (not name[0].isupper()) and (name not in BaseApi.RESERVED_METHODS):
                namespace[name] = getattr(self, name)
        return namespace
    def namespace(self):
        return self._namespace
    def checkAborted(self):
        if self._aborted==True:
            print "script aborting..."
            raise AbortedException(time.time())
        return False
    def abort(self):
        print "aborting script if possible..."
        self._aborted = True
    def sleep(self, duration):
        if not duration:
            return
        maxTime = time.time()+duration
        while time.time()<maxTime:
            self.checkAborted()
            time.sleep(0.1)
