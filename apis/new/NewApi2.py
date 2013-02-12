'''
Created on 3 Dec 2012

@author: francis
'''

class NewApi2(object):
    NAMESPACE = "Daphne"
    NAME = "new-stbtester-api2"
    VERSION = 1.0
    def stuff(self, s):
        self._debugger.debug(s)
    def aDifferentMethod(self):
        return 2
