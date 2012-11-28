'''
Created on 9 Nov 2012

@author: francis
'''

from StbTester.core.events.Event import Event

class RunnerEvent(Event):
    PREFIX = "RUNNER"
    def __str__(self):
        action = self.action()
        results = ""
        if action=="Results":
            results = "... "+self._formatResults(self.args())
        result = "%(T)s RunnerEvent: %(N)s%(R)s"%{"N":action, "T":self.timestamp(), "R":results}
        return result
    @staticmethod
    def _formatResults(args):
        s = [""]
        results = args[0]
        for name, result in results.items():
            s.append("%(N)s => %(R)s"%{"N":name, "R": result})
        ss = ", ".join(s)
        return ss
    def action(self):
        return self.name().split("-")[1].title()
