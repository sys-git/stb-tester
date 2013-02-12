'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.core.debugging.Debugger import Debugger
from StbTester.remotes.impls.lirc.LircRemote import LircRemote
from StbTester.remotes.impls.virtual.VirtualRemote import VirtualRemote
from test.utils.FakeLircd import FakeLircd
import tempfile
import threading
import time
import unittest

class Test(unittest.TestCase):
    def setUp(self):
        self._debugger = Debugger(level=2)
    def test_that_lirc_remote_is_symmetric_with_lirc_remote_listen(self):
        lircd_socket = tempfile.mktemp()
        t = threading.Thread()
        t.run = lambda: FakeLircd(lircd_socket)
        t.start()
        time.sleep(0.01)  # Give it a chance to start listening (sorry)
        listener = LircRemote.listen(lircd_socket, 'test', self._debugger)
        control = LircRemote(lircd_socket, 'test', self._debugger)
        for i in ['DOWN', 'DOWN', 'UP', 'GOODBYE']:
            control.press(i)
            assert listener.next() == i
        control.close()
        t.join()
    def test_that_virtual_remote_is_symmetric_with_virtual_remote_listen(self):
        received = []
        keys = ['DOWN', 'DOWN', 'UP', 'GOODBYE']
        def listener():
            #    "* 2" is once for VirtualRemote's __init__ and once for press.
            for _ in range(len(keys) * 2):
                for k in VirtualRemote.listen('localhost', 2033, self._debugger):
                    received.append(k)
        t = threading.Thread()
        t.run = listener
        t.start()
        for k in keys:
            time.sleep(0.01)  # Give listener a chance to start listening (sorry)
            vr = VirtualRemote('localhost', 2033, self._debugger)
            time.sleep(0.01)
            vr.press(k)
        t.join()
        assert received == keys

if __name__ == '__main__':
    unittest.main()
