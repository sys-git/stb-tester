'''
Created on 3 Dec 2012

@author: francis
'''

from StbTester.apis.impls.common.BaseApi import BaseApi

class EmptyApi(BaseApi):
    def __init__(self, *args, **kwargs):
        super(EmptyApi, self).__init__(None, None, None, None)
    def requires(self, *args, **kwargs):
        pass
