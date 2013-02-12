'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.apis.ApiHelper import ApiHelper
from StbTester.core.errors.DuplicateApiNamespaceError import \
    DuplicateApiNamespaceError
from StbTester.core.errors.InsufficientlySpecifiedApiLoad import \
    InsufficientlySpecifiedApiLoad
from StbTester.core.errors.UnknownApiError import UnknownApiError

class ApiFactory(object):
    _map = []
    @staticmethod
    def __new__(cls, type_):
        try:
            return ApiFactory._find(type_)
        except Exception, _e:
            raise UnknownApiError(type_)
    @classmethod
    def emptyApi(cls, type_):
        try:
            return ApiFactory._find(type_)
        except Exception, _e:
            raise UnknownApiError(type_)
    @staticmethod
    def create(apiTypes, allowDuplicates=False):
        r"""
        @summary: Import an api type from the file-system.
        """
        for type_ in apiTypes:
            apid = ApiHelper.loadApiType(type_)
            if allowDuplicates==False:
                try:
                    ApiFactory._find(type_)
                except Exception, _e:
                    pass
                else:
                    raise DuplicateApiNamespaceError([apid.ns()])
            ApiFactory._map.append(apid)
    @staticmethod
    def _find(type_):
        #    All non-None fields must match exactly!
        if len(ApiFactory._map)==0:
            raise Exception("No apis loaded!")
        #    If multiple, raise InsufficientlySpecifiedApi(type_, [matching apis]).
        apid = ApiHelper.decodeApiType(type_)
        matching = []
        for item in ApiFactory._map:
            match = True
            for matcher in ["apiType", "clazzName", "ns", "path"]:
                attr = getattr(apid, matcher)()
                if attr!=None:
                    if getattr(item, matcher)()!=attr:
                        match = False
                        break
            if match==True:
                matching.append(item)
        if len(matching)>1:
            raise InsufficientlySpecifiedApiLoad(type_, matching)
        return matching[0]
