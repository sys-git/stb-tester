'''
Created on 31 Oct 2012

@author: YouView
'''

import gobject

class GObjectTimeout(object):
    """
    Responsible for setting a timeout in the GTK main loop.
    Can be used as a Context Manager in a 'with' statement.
    """
    def __init__(self, timeoutSecs, handler, *args):
        self._timeoutSecs = timeoutSecs
        self._handler = handler
        self._args = args
        self._timeoutId = None
    def __enter__(self):
        self.start()
        return self
    def __exit__(self, type_, value, traceback):
        self.cancel()
    def start(self):
        self._timeoutId = gobject.timeout_add(self._timeoutSecs*1000, self._handler, *self._args)
    def cancel(self):
        if self._timeoutId:
            gobject.source_remove(self._timeoutId)
        self._timeoutId = None
