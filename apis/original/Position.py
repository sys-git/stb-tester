'''
Created on 31 Oct 2012

@author: YouView
'''

from collections import namedtuple

class Position(namedtuple('Position', 'x y')):
    """
    * `x` and `y`: Integer coordinates from the top left corner of the video
      frame.
    """
    pass

