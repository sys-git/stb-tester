'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.core.errors.UnknownApiError import UnknownApiError

class MalformdedApiError(UnknownApiError):
    def __init__(self, api, token=None):
        super(MalformdedApiError, self).__init__(api)
        self.api = api
        self.token = token
