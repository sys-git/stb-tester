'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.apis.ApiType import ApiType
from StbTester.apis.impls.original.OriginalApi import OriginalApi
from StbTester.core.errors.UnknownApiError import UnknownApiError

class ApiFactory(object):
    @staticmethod
    def __new__(cls, type_):
        if type_==ApiType.ORIGINAL:
            return OriginalApi
        raise UnknownApiError(type_)
    @classmethod
    def emptyApi(cls, type_):
        if type_==ApiType.ORIGINAL:
            return OriginalApi.EMPTY()
        raise UnknownApiError(type_)
