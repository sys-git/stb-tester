'''
Created on 9 Nov 2012

@author: francis
'''

from StbTester.core.utils.TimeUtils import timestamp
import time

class Event(object):
    def __init__(self, name, *args, **kwargs):
        self._name = name
        self._time = time.time()
        self._args = args
        self._kwargs = kwargs
    def name(self):
        return self._name
    def time(self):
        return self._time
    def args(self):
        return self._args
    def kwargs(self):
        return self._kwargs
    def timestamp(self):
        return timestamp(self.time())
    def __str__(self):
        return "%(T)s Event: %(N)s"%{"N":self.name(), "T":self.timestamp()}
