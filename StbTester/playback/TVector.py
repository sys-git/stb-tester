'''
Created on 26 Nov 2012

@author: francis
'''
import os

class TVector(object):
    def __init__(self, methodName=None, moduleSig=None, filename=None, root=None, nose=False):
        self._methodName = methodName
        self._moduleSig = moduleSig
        self._filename = filename
        self._root = root
        self._nose = nose
    def methodName(self, defaultValue=None):
        if self._methodName==None:
            return defaultValue
        return self._methodName
    def moduleSig(self):
        return self._moduleSig
    def filename(self):
        return self._filename
    def root(self):
        return self._root
    def nose(self):
        return self._nose
    def __str__(self):
        if self._methodName!=None:
            return "%(F)s:%(M)s"%{"F":self.getRelPath(), "M":self._methodName}
        return self.getRelPath()
    def getRelPath(self):
        return self._filename.partition(self._root+os.sep)[2]
    def getRelModule(self):
        p = self.getRelPath()
        name = os.path.splitext(os.path.basename(p))[0]
        dirname = os.path.dirname(p)
        return dirname+"."+name
