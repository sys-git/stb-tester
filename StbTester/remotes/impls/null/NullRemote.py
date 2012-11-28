'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.remotes.impls.BaseRemote import BaseRemote

class NullRemote(BaseRemote):
    def press(self, key):
        self._debugger.debug('NullRemote: Ignoring request to press "%s"'%key)

