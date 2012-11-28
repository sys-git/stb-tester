'''
Created on 8 Nov 2012

@author: francis
'''

class Command(object):
    def __init__(self, cmd, uId, data=None):
        self.cmd = cmd
        self.uId = uId
        self.data = data

