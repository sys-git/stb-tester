
from Irnetbox import RemoteControlConfig
from StbTester.remotes.impls.BaseRemote import BaseRemote
from StbTester.remotes.impls.irnetbox.Irnetbox import IRNetBox
import socket
import time

class IRNetBoxRemote(BaseRemote):
    """
    Send a key-press via the network-controlled RedRat IRNetBox IR emitter.
    See http://www.redrat.co.uk/products/irnetbox.html
    """
    def __init__(self, hostname, output, configFile, debugger):
        self.hostname = hostname
        self.output = int(output)
        self.config = RemoteControlConfig(configFile)
        # Connect once so that the test fails immediately if irNetBox not found
        # (instead of failing at the first `press` in the script).
        self._debugger.debug("IRNetBoxRemote: Connecting to %s" % hostname)
        with self._connect() as irnb:
            irnb.power_on()
        time.sleep(0.5)
        self._debugger.debug("IRNetBoxRemote: Connected to %s" % hostname)

    def press(self, key):
        with self._connect() as irnb:
            irnb.irsend_raw(
                port=self.output, power=100, data=self.config[key])
        time.sleep(0.5)
        self._debugger.debug("Pressed " + key)

    def _connect(self):
        try:
            return IRNetBox(self.hostname)
        except socket.error as e:
            e.args = (("Failed to connect to IRNetBox %s: %s" % (self.hostname, e)),)
            e.strerror = e.args[0]
            raise
