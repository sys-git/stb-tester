'''
Created on 6 Nov 2012

@author: francis
'''

from StbTester.core.errors.DuplicateApiError import DuplicateApiError
from StbTester.core.errors.MaskedAttributeError import MaskedAttributeError
from StbTester.core.namespace.NamespaceWrapper import NamespaceWrapper
from StbTester.core.namespace.NamespaceWrapperController import \
    NamespaceWrapperController
import threading
import time
import unittest

class TestingNamespaceWrapper(NamespaceWrapper):
    def __init__(self, *args, **kwargs):
        super(TestingNamespaceWrapper, self).__init__(*args, **kwargs)
    def b(self):
        print "nsw-b"
        return "nsw-b"
    def aa(self):
        print "nsw-aa"
        return "nsw-aa"
    def a(self):
        print "nsw-a"
        return "nsw-a"

class Test(unittest.TestCase):
    def testInsertApi(self, method=None, eResult="test-ccc", waitOnEvent=False):
        if method==None:
            def ccc():
                print eResult
                return eResult
            method = ccc
        self.ns = {"cc":method}
        self.nsc = NamespaceWrapperController.create(self.ns, TestingNamespaceWrapper, waitOnEvent=waitOnEvent)
        wrapper = self.nsc.getWrapper()
        #    Positive case:
        result = wrapper.cc()
        assert result==eResult
        #    Insert duplicate apis:
        eResultDD = "test-dd"
        eResultEE = "test-ee"
        def dd():
            msg = eResultDD
            print msg
            return msg
        def ee():
            msg = eResultEE
            print msg
            return msg
        newApi = {"dd":dd, "ee":ee, "cc":method}
        try:
            self.nsc.insertApi(newApi)
        except DuplicateApiError, e:
            names = e.names()
            assert len(names)==1
            assert "cc" in names
        #    Insert non-duplicate apis:
        newApi.pop("cc")
        self.nsc.insertApi(newApi)
        #    Now call the new api methods:
        for method, eResult in [(wrapper.dd, eResultDD), (wrapper.ee, eResultEE)]:
            result = method()
            assert result==eResult
    def testMaskedMethod(self):
        #    Check masked attributes:
        for ns in [{"b":1}, {"aa":2}, {"a":3}]:
            try:
                NamespaceWrapperController.create(ns, TestingNamespaceWrapper, waitOnEvent=False)
            except MaskedAttributeError, _e:
                assert True
            else:
                assert False
    def testUnmaskedMethod(self, waitOnEvent=False, method=None, eResult="test-bbb", timeout=None):
        if method==None:
            def bbb():
                print "bbb"
                return eResult
            method = bbb
        self.ns = {"bb":method}
        self.nsc = NamespaceWrapperController.create(self.ns, TestingNamespaceWrapper, waitOnEvent=waitOnEvent)
        self.nsw = self.nsc.getWrapper()
        if waitOnEvent==True:
            threading.Timer(timeout, self.nsc.run).start()
        result = self.nsw.bb()
        print "result: ", result
        assert result==eResult
    def testUnmaskedMethodWithEventRelease(self):
        timeout = 2
        eResult = "newMethod"
        calledTime = {}
        startTime = time.time()
        def newMethod():
            print eResult
            calledTime["t"] = time.time()
            return eResult
        self.testUnmaskedMethod(waitOnEvent=True, method=newMethod, eResult=eResult, timeout=timeout)
        timeNow = time.time()
        timeDelta = timeNow-calledTime["t"]
        print "calledTime: ", calledTime
        assert calledTime["t"]-startTime<1
        assert timeDelta>0
        safety = 1
        assert timeDelta<timeout+safety 

if __name__ == '__main__':
    unittest.main()
