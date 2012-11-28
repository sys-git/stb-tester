'''
Created on 8 Nov 2012

@author: francis
'''

from StbTester.playback.results.BaseResult import BaseResult

class NoResult(BaseResult):
    def __str__(self):
        return "NoResult"
