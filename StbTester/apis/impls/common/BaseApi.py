'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.apis.impls.common.errors.AbortedException import AbortedException
from StbTester.apis.impls.common.errors.ApiRequiredFailure import \
    ApiRequiredFailure
import time

class BaseApi(object):
    r"""
    @attention: APIs have the following requirements.
    All public methods:
        1.    Do not begin with an underscore.
        2.    Do not begin with an upper-case character.
        3.    Do not include any of the reserved methods: BaseApi.RESERVED_METHODS
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
            self._debugger.debug("script aborting...")
            raise AbortedException(time.time())
        return False
    def abort(self):
        self._debugger.debug("aborting script if possible...")
        self._aborted = True
    def sleep(self, duration):
        if not duration:
            return
        maxTime = time.time()+duration
        while time.time()<maxTime:
            self.checkAborted()
            time.sleep(0.1)
    @classmethod
    def requires(cls, whats):
        r"""
        @summary: Provides a check that a test can perform to make sure the correct
        api(s) are being used.
        @param whats: list[dict{"ns":www, "name":xxx, "min":yyy, "max":zzz, "exact":abc}]
        @return: None.
        @raise ApiRequiredFailure: API requirements not met.
        """
        if not isinstance(whats, list):
            whats = [whats]
        found = False
        for what in whats:
            name = what.get("name", None)
            ns = what.get("ns", None)
            minVersion = what.get("min", None)
            maxVersion = what.get("max", None)
            exactVersion = what.get("exact", None)
            err = ApiRequiredFailure({ns:what}, whats)
            nameMatch = True
            nsMatch = True
            if name!=None:
                nameMatch = (cls.NAME.strip().lower()==name.strip().lower())
            if ns!=None:
                nsMatch = (cls.NAMESPACE.strip()==ns.strip())
            if (nameMatch==True) and (nsMatch==True):
                #    Now check the versions:
                if minVersion!=None:
                    if cls.VERSION<minVersion:
                        continue
                if maxVersion!=None:
                    if cls.VERSION>maxVersion:
                        continue
                if exactVersion!=None:
                    if cls.VERSION!=exactVersion:
                        continue
                found = True
                break
        if found==False:
            raise err
    @classmethod
    def EMPTY(cls):
        return cls(None, None, None, None)
