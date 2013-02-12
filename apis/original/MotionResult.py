'''
Created on 31 Oct 2012

@author: YouView
'''

from collections import namedtuple

class MotionResult(namedtuple('MotionResult', 'timestamp motion')):
    """
    * `timestamp`: Video stream timestamp.
    * `motion`: Boolean result.
    """
    pass
