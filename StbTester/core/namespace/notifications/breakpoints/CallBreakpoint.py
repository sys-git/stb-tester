'''
Created on 22 Nov 2012

@author: francis
'''

class CallBreakpoint(object):
    def __init__(self, name, apid, args, kwargs):
        self._name = name
        self._apid = apid
        self._args = args
        self._kwargs = kwargs
    def name(self):
        return self._name
    def apid(self):
        return self._apid
    def args(self):
        return self._args
    def kwargs(self):
        return self._kwargs
