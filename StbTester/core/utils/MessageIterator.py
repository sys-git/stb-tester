'''
Created on 31 Oct 2012

@author: YouView
'''

import Queue

def MessageIterator(bus, signal, mainloop, checkAborted=lambda: False):
    queue = Queue.Queue()
    def sig(bus, message):
        queue.put(message)
        mainloop.quit()
    bus.connect(signal, sig)
    try:
        while not checkAborted():
            mainloop.run()
            # Check what interrupted the main loop (new message, error thrown)
            try:
                item = queue.get(block=False)
                yield item
            except Queue.Empty:
                checkAborted = lambda: True
    finally:
        bus.disconnect_by_func(sig)

