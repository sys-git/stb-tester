'''
Created on 26 Nov 2012

@author: francis
'''

import unittest

def aTestmethod():
    pass

class aTestClass(unittest.TestCase):
    def setUp(self):
        __loads__(["apis/original/OriginalApi?clazz=TheApi?ns=api"])      #@UndefinedVariable
    def tearDown(self):
        pass
    def testMethodInClass(self):
        print "test5 start!"
        api.press("15")                                      #@UndefinedVariable
        print "test5 end!"

if __name__ == '__main__':
    unittest.main()
