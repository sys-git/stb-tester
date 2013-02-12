'''
Created on 4 Dec 2012

@author: francis
'''

from StbTester.apis.ApiDescription import ApiDescription
from StbTester.core.errors import MalformedApiError
from StbTester.core.utils.ImportUtils import importModule
import os
import sys
from StbTester.apis.impls.common.BaseApi import BaseApi
from StbTester.apis.impls.common.errors.ApiSpecificationInvalid import ApiSpecificationInvalid

class ApiHelper(object):
    @staticmethod
    def _decodeToken(s, token):
        name, match, value = token.partition("=")
        if match and value:
            return (name, value)
        raise MalformedApiError(s, token)
    @staticmethod
    def loadApiType(apiType, apids=[], root=None):
        apid = ApiHelper.decodeApiType(apiType, root=root).parse()
        if root!=None and not os.path.isabs(apid.path()):
            path = os.path.join(root, apid.path())
            apid.setPath(path)
        else:
            path = apid.path()
        path = os.path.realpath(os.path.dirname(path))
        sys.path.append(path)
        apid.setApi(importModule(apid.moduleName(), apid.clazzName(), apids=(apid, apids)))
        sys.path.pop()
        #    Now the module is loaded we can do funky stuff to it like create a
        #    new type based on a BaseApi superclass...
        api = apid.api()
        #    If the api does NOT inherit from BaseApi, make it:
        if (object not in api.__bases__) and (BaseApi not in api.__bases__):
            raise ApiSpecificationInvalid(os.path.realpath(apid.path()))
        if BaseApi not in api.__bases__:
            #    Make it so!
            clazzName = apid.clazzName()
            newApi = type(clazzName, (api, BaseApi, object), {})
            apid.setApi(newApi)
            print "warning: api %(M)s.%(C)s now inherits from BaseApi"%{"M":apid.moduleName(), "C":apid.clazzName()}
        ns = apid.ns()
        api = apid.api()
        if ns!=None:
            #    Override the api's namespace:
            api.NAMESPACE = ns
        else:
            #    Use the api's namespace:
            apid.setNs(api.NAMESPACE)
        return apid
    @staticmethod
    def decodeApiType(apiType, root=None):
        r"""
        @attention: path = str(<?class=xxx><?ns=yyy>)
        if the class is not specified use the filename.
        if the ns is specified, use this instead of the type's one.
        """
        s = apiType.strip()
        tokens = s.split("?")
        if len(tokens)==1:
            if len(tokens[0])==0:
                raise MalformedApiError(s)
            if (s.find("$")!=-1):
                raise MalformedApiError(s)
            return ApiDescription(apiType, tokens[0], root=root)
        kwargs = {}
        for token in tokens[1:]:
            (name, value) = ApiHelper._decodeToken(s, token)
            kwargs[name] = value
        try:
            return ApiDescription(apiType, tokens[0], root=root, **kwargs)
        except TypeError:
            raise MalformedApiError(s)
