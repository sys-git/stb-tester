'''
Created on 2 Nov 2012

@author: YouView
'''

from StbTester.apis.impls.common.errors.UITestError import UITestError

class ApiRequiredFailure(UITestError):
    def __init__(self, *args, **kwargs):
        super(ApiRequiredFailure, self).__init__(*args, **kwargs)
        provided = args[0]
        self.provided = provided 
        self.requires = args[1]
    def provided(self):
        return self.provided
    def requires(self):
        return self.requires
    def __str__(self):
        s = ["Available APIs:"]
        for ns, i in self.provided.items():
            s.append("ns: '%(NS)s' %(A)s', version: '%(V)s'"%{"NS":ns, "A":i["name"], "V":i["version"]})
        s.append("but requires: ")
        ss = []
        for i in self.requires:
            k = []
            if "name" in i:
                k.append("name: '%(M)s'"%{"M":i["name"]})
            if "min" in i:
                k.append("min: '%(M)s'"%{"M":i["min"]})
            if "max" in i:
                k.append("max: '%(M)s'"%{"M":i["max"]})
            if "exact" in i:
                k.append("exact: '%(M)s'"%{"M":i["exact"]})
            ss.append("["+", ".join(k)+"]")
        s.append(", ".join(ss))
        return " ".join(s)
