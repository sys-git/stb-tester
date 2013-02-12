'''
Created on 3 Dec 2012

@author: francis
'''

class NewApi(object):
    NAMESPACE = "Daphne"
    NAME = "new-stbtester-api"
    VERSION = 1.0
    def __init__(self, *args, **kwargs):
        super(NewApi, self).__init__(*args, **kwargs)
        self.STORE = None
    def stuff(self, s):
        self._debugger.debug(s)
    def store(self, value):
        self.STORE = value
    def getStore(self):
        return self.STORE