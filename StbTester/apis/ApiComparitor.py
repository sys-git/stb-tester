'''
Created on 4 Dec 2012

@author: francis
'''

from StbTester.apis.impls.common.errors.ApiRequiredFailure import \
    ApiRequiredFailure
from StbTester.core.namespace.notifications.api.ApiRequires import ApiRequires
from StbTester.playback.commands.RunnerCommand import Command
from StbTester.playback.commands.TRCommands import TRCommands
import inspect
import time

class ApiComparitor(object):
    def __init__(self, scriptName=None, apids=[], uId=None, q=None):
        self._scriptName = scriptName
        self.apids = apids
        self._uId = uId
        self._q = q
    def __call__(self, whats=[]):
        r"""
        @summary: Check that all the required apis are present and correct as
        required.
        @return: dict{NS:{"name", "version"}
        """
        callers = inspect.stack()
        frame = callers[1]
        filename = frame[1]
        lineNumber = frame[2]
        result = {}
        for apid in self.apids:
            api = apid.api()
            ns = apid.ns()
            result[ns] = {"ns":ns,
                          "name":api.NAME,
                          "version":api.VERSION,
                          "path":apid.path(),
                          "module":apid.moduleName(),
                          "clazz":apid.clazzName(),
                          "original_ns":apid.originalNs()}
        if not isinstance(whats, list):
            whats = [whats]
        newWhats = []
        for what in whats:
            if what!=None:
                newWhats.append(what)
        #    Does 'what' exist in any of apids?
        for what in newWhats:
            try:
                found = False
                for apid in self.apids:
                    api = apid.api()
                    try:
                        api.requires(what)
                    except ApiRequiredFailure, _e:
                        pass
                    else:
                        found = True
                        break
                if found==False:
                    raise ApiRequiredFailure(result, [what])
            except Exception, r:
                raise
            else:
                r = None
            finally:
                if self._q!=None:
                    self._q.put(Command(TRCommands.API_REQUIRES, self._uId, data=ApiRequires(self._scriptName, time.time(), whats, apid, r, callers[1:], filename, lineNumber)))
        return result
