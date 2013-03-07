'''
Created on 3 Dec 2012

@author: francis
'''

class NewApi1(object):
    NAMESPACE = "Daphne"
    NAME = "new-stbtester-api1"
    VERSION = 1.0
    def __init__(self, *args, **kwargs):
        super(NewApi1, self).__init__(*args, **kwargs)
        self.STORE = None
    def stuff(self, s):
        self._debugger.debug(s)
    def aDifferentMethod(self):
        return 1
    def store(self, value):
        self.STORE = value
    def getStore(self):
        return self.STORE
