'''
Created on 8 Nov 2012

@author: francis
'''

from StbTester.apis.impls.common.errors.UITestError import UITestError

class AbortedException(UITestError):
    def __str__(self):
        return "Aborted @ %(M)s"%{"M":self.message}
