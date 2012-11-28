'''
Created on 31 Oct 2012

@author: YouView
'''

import os
import sys

class Debugger(object):
    """
    Single output sink for all application logging.
    """
    def __init__(self, level):
        self._debugLevel = level
    def level(self):
        return self._debugLevel
    def debug(self, s):
        if self._debugLevel > 0:
            sys.stderr.write("%s: %s\n"%(os.path.basename(sys.argv[0]), str(s)))
    def ddebug(self, s):
        """Extra verbose debug for stbt developers, not end users"""
        if self._debugLevel > 1:
            sys.stderr.write("%s: %s\n"%(os.path.basename(sys.argv[0]), str(s)))
    def warn(self, s):
        sys.stderr.write("%s: warning: %s\n"%(os.path.basename(sys.argv[0]), str(s)))
    def error(self, s):
        sys.stderr.write("%s: error: %s\n"%(os.path.basename(sys.argv[0]), str(s)))

