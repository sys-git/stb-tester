'''
Created on 31 Oct 2012

@author: YouView
'''

from collections import namedtuple

class MatchResult(
    namedtuple('MatchResult', 'timestamp match position first_pass_result')):
    """
    * `timestamp`: Video stream timestamp.
    * `match`: Boolean result.
    * `position`: `Position` of the match.
    * `first_pass_result`: Value between 0 (poor) and 1.0 (excellent match)
      from the first pass of the two-pass templatematch algorithm.
    """
    pass
