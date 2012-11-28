'''
Created on 1 Nov 2012

@author: YouView
'''

import sys

class ArgvHider:
    """
    For use with 'with' statement:  Unsets argv and resets it.
    This is used because otherwise gst-python will exit if '-h', '--help', '-v'
    or '--version' command line arguments are given.
    """
    def __enter__(self):
        self.argv = sys.argv[:]
        del sys.argv[1:]
    def __exit__(self, type_, value, traceback):
        sys.argv = self.argv
