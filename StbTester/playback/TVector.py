'''
Created on 26 Nov 2012

@author: francis
'''
import os

class TVector(object):
    def __init__(self, methodName=None, moduleSig=None, filename=None, root=None):
        self._methodName = methodName
        self._moduleSig = moduleSig
        self._filename = filename
        self._root = root
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
    def __str__(self):
        if self._methodName!=None:
#            if self._methodName.find(".")==-1:
#                return "%(F)s.%(M)s"%{"F":self.getRelModule(), "M":self._methodName}
            return "%(F)s:%(M)s"%{"F":self.getRelPath(), "M":self._methodName}
        return self.getRelPath()
    def getRelPath(self):
        return self._filename.partition(self._root+os.sep)[2]
    def getRelModule(self):
        p = self.getRelPath()
        name = os.path.splitext(os.path.basename(p))[0]
        dirname = os.path.dirname(p)
        return dirname+"."+name
