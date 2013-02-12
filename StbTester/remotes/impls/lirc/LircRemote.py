'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.remotes.impls.BaseRemote import BaseRemote
import socket
import re

class LircRemote(BaseRemote):
    """
    Send a key-press via a LIRC-enabled infrared blaster.
    See http://www.lirc.org/html/technical.html#applications
    """
    CONNECT_TIMEOUT = 3
    def __init__(self, lircdSocket, controlName, debugger):
        super(LircRemote, self).__init__(debugger)
        self._controlName = controlName
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._debugger.debug("LircRemote: Connecting to %s" % lircdSocket)
        try:
            self._sock.settimeout(LircRemote.CONNECT_TIMEOUT)
            self._sock.connect(lircdSocket)
            self._sock.settimeout(None)
            self._debugger.debug("LircRemote: Connected to %s" % lircdSocket)
        except socket.error as e:
            e.args = (("Failed to connect to Lirc socket %s: %s"%(lircdSocket, e)),)
            e.strerror = e.args[0]
            raise
    def press(self, key):
        self._sock.sendall("SEND_ONCE %s %s\n"%(self._controlName, key))
        self._debugger.debug("Pressed " + key)
    def close(self):
        self._sock.close()
        self._sock = None
    @staticmethod
    def listen(lircdSocket, controlName, debugger):
        """
        Returns an iterator yielding key presses received from lircd.

        See http://www.lirc.org/html/technical.html#applications
        """
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        debugger.debug("control-recorder connecting to lirc socket '%s'..." % lircdSocket)
        sock.connect(lircdSocket)
        debugger.debug("control-recorder connected to lirc socket")
        return LircRemote.keyreader(sock.makefile(), controlName, debugger)
    @staticmethod
    def keyreader(cmdIter, controlName, debugger):
        r"""
        Convert lircd messages into list of keypresses

        >>> list(lirc_key_reader(['0000dead 00 MENU My-IR-remote',
        ...                       '0000beef 00 OK My-IR-remote',
        ...                       '0000f00b 01 OK My-IR-remote',
        ...                       'BEGIN', 'SIGHUP', 'END'],
        ...                      'My-IR-remote'))
        ['MENU', 'OK']
        """
        for s in cmdIter:
            debugger.debug("lirc_key_reader received: %s" % s.rstrip())
            m = re.match(r"\w+ (?P<repeat_count>\d+) (?P<key>\w+) %s"%controlName,s)
            if m and int(m.group('repeat_count'))==0:
                yield m.group('key')




