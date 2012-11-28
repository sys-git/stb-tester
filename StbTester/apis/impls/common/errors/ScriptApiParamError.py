'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.apis.impls.common.errors.UITestError import UITestError

class ScriptApiParamError(UITestError):
    def __init__(self, method, param, value, expectedTypesTuple):
        super(ScriptApiParamError, self)._init__()
        self._method = method
        self._param = param
        self._value = value
        self._expectedTypes = expectedTypesTuple
    def method(self):
        return self._method
    def param(self):
        return self._param
    def value(self):
        return self._value
    def expectedTypes(self):
        return self._expectedTypes
    def __str__(self):
        return " ".join([
                          "ScriptApiParamError:",
                          "%(M)s(%(P)s=%(V)s, ...)"%{"M":self._method, "P":self._param, "V":self._value},
                          "AllowedTypes: %(A)s"%{"A":self._expectedTypesTuple},
                          ])
