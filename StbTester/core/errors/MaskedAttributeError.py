'''
Created on 6 Nov 2012

@author: francis
'''

from StbTester.core.errors.UiError import UiError

class MaskedAttributeError(UiError, AttributeError):
    pass
