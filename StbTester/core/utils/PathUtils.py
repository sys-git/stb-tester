'''
Created on 31 Oct 2012

@author: YouView
'''

import errno
import inspect
import os

def mkdir(d):
    try:
        os.makedirs(d)
    except OSError, e:
        if e.errno != errno.EEXIST:
            return False
    return os.path.isdir(d) and os.access(d, os.R_OK | os.W_OK)

def findPath(image):
    """
    Searches for the given filename and returns the full path.
    Searches in the directory of the script that called (for example)
    detect_match, then in the directory of that script's caller, etc.
    """
    if os.path.isabs(image):
        return image
    # stack()[0] is _find_path;
    # stack()[1] is _find_path's caller, e.g. detect_match;
    # stack()[2] is detect_match's caller (the user script).
    for caller in inspect.stack()[2:]:
        filename = inspect.getframeinfo(caller[0]).filename
        if filename=="<string>":
            dirname = caller[0].f_globals["__srcdir__"]
        else:
            dirname = os.path.dirname(filename)
        caller_image = os.path.join(
            dirname,
            image)
        if os.path.isfile(caller_image):
            return os.path.abspath(caller_image)
    # Fall back to image from cwd, for convenience of the tests
    return os.path.abspath(image)
