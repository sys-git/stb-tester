'''
Created on 12 Nov 2012

@author: francis
'''

import sys

def importModule(where, what, apids=None):
    if what not in sys.modules:
        module_ = __import__(where, globals(), locals(), [what], -1)
    else:
        module_ = sys.modules[what]
        if apids!=None:
            (apid, apids) = apids
            #    Find the same api's existing originalNs:
            for a in apids:
                if a.clazzName()==apid.clazzName() and a.path()==apid.path():
                    apid.setOriginalNs(a.originalNs())
                    break
    return getattr(module_, what)

def getClass(kls):
    parts = kls.split('.')
    module_ = ".".join(parts[:-1])
    m = __import__(module_)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m

def importModuleName(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
