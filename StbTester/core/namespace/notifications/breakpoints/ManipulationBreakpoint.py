'''
Created on 7 Feb 2013

@author: francis
'''

class ManipulationBreakpoint(object):
    def __init__(self, whats, mode):
        self._whats = whats
        self._mode = mode
    def whats(self):
        return self._whats
    def mode(self):
        return self._mode
