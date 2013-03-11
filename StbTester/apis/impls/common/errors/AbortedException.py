'''
Created on 8 Nov 2012

@author: francis
'''

from StbTester.apis.impls.common.errors.UITestError import UITestError
from StbTester.core.utils.TimeUtils import timestamp

class AbortedException(UITestError):
    def __str__(self):
        return "Aborted @ %(M)s"%{"M":timestamp(self.message)}
