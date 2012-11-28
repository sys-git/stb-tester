'''
Created on 1 Nov 2012

@author: YouView
'''

class BaseRemote(object):
    def __init__(self, debugger):
        self._debugger = debugger
    def teardown(self):
        r"""
        Override this as necessary.
        """
        pass
