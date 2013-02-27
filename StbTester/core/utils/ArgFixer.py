'''
Created on 27 Feb 2013

@author: francis
'''

import shlex

class ArgFixer(object):
    @staticmethod
    def fixBoolAttr(what, name):
        if getattr(what, name)=="False":
            setattr(what, name, False)
        elif getattr(what, name)=="True":
            setattr(what, name, True)
    @staticmethod
    def fixAttr(what):
        if not isinstance(what, list):
            what = [what]
            if len(what)>0:
                newWhat = []
                for lib in what:
                    for thingy in shlex.split(lib):
                        newWhat.append(thingy)
                what = newWhat
        return what
