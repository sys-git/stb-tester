'''
Created on 4 Dec 2012

@author: francis
'''

import os

class ApiDescription(object):
    def __init__(self, apiType, path, clazz=None, ns=None, root=None):
        #    We later need the actual unique file - the real file irrespective of symbolic linkage or separator.
        if root!=None and not os.path.isabs(path):
            path = os.path.join(root, path)
        self._path = os.path.realpath(os.path.normpath(path))
        #    The actual string used to create this api (useful if clashing namespaces).
        self._apiType = apiType
        self._clazz = clazz
        self._originalNs = None
        self._ns = ns
        self._api = None
    def apiType(self):
        return self._apiType
    def setPath(self, path):
        self._path = path
    def path(self):
        return self._path
    def parse(self):
        #    The ns is the ns of the api once imported unless set here.
        if self._clazz==None:
            #    Class is the name of the file:
            self._clazz = os.path.basename(self._path)
        return self
    def moduleName(self):
        return os.path.basename(self._path)
    def clazzName(self):
        return self._clazz
    def api(self):
        return self._api
    def setApi(self, api):
        self._api = api
        #    If this is a re-import, don't change the original namespace:
        if self._originalNs==None:
            self._originalNs = self._api.NAMESPACE
    def ns(self):
        return self._ns
    def originalNs(self):
        return self._originalNs
    def setOriginalNs(self, originalNs):
        self._originalNs = originalNs
    def setNs(self, ns):
        self._ns = ns
    def __eq__(self, other):
        if not isinstance(other, ApiDescription):
            return False
        if other.path()!=self.path():
            return False
        if other.moduleName()!=self.moduleName():
            return False
        if other.clazzName()!=self.clazzName():
            return False
        if other.ns()!=self.ns():
            return False
        return True








