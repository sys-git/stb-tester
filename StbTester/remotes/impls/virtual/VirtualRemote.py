'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.remotes.impls.BaseRemote import BaseRemote
import socket

class VirtualRemote(BaseRemote):
    """
    Send a key-press to a set-top box running a VirtualRemote listener.
    control = VirtualRemote("192.168.0.123")
    control.press("MENU")
    """
    CONNECT_TIMEOUT = 3
    def __init__(self, hostname, port, debugger):
        super(VirtualRemote, self).__init__(debugger)
        self._sock = socket.socket()
        self._debugger.debug("VirtualRemote: Connecting to %s:%d"%(hostname, port))
        try:
            self._sock.settimeout(VirtualRemote.CONNECT_TIMEOUT)
            self._sock.connect((hostname, port))
            self._sock.settimeout(None)
            self._debugger.debug("VirtualRemote: Connected to %s:%d"%(hostname, port))
        except socket.error as e:
            e.args = (("Failed to connect to VirtualRemote at %s:%d: %s"%(hostname, port, e)),)
            e.strerror = e.args[0]
            raise
    def press(self, key):
        self._sock.send("D\t%s\n\0U\t%s\n\0"%(key, key))  # key Down, then key Up
        self._debugger.debug("Pressed "+key)
    def close(self):
        self._sock.close()
        self._sock = None
    @staticmethod
    def listen(address, port, debugger):
        """
        Waits for a VirtualRemote to connect, and returns an iterator yielding
        keypresses."""
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind((address, port))
        serversocket.listen(5)
        debugger.debug("Waiting for connection from virtual remote control "
                         "on %s:%d...\n" % (address, port))
        (connection, address) = serversocket.accept()
        debugger.debug("Accepted connection from %s\n" % str(address))
        return VirtualRemote.keyReader(VirtualRemote.readRecords(connection, '\n\0'))
    @staticmethod
    def keyReader(cmdIter):
        r"""
        Converts virtual remote records into list of keypresses
        >>> list(vr_key_reader(['D\tHELLO', 'U\tHELLO']))
        ['HELLO']
        >>> list(vr_key_reader(['D\tCHEESE', 'D\tHELLO', 'U\tHELLO', 'U\tCHEESE']))
        ['HELLO', 'CHEESE']
        """
        for i in cmdIter:
            (action, key) = i.split('\t')
            if action=='U':
                yield key
    @staticmethod
    def readRecords(stream, sep):
        r"""
        Generator that splits stream into records given a separator
        >>> import StringIO
        >>> s = StringIO.StringIO('hello\n\0This\n\0is\n\0a\n\0test\n\0')
        >>> list(read_records(FileToSocket(s), '\n\0'))
        ['hello', 'This', 'is', 'a', 'test']
        """
        buf = ""
        while True:
            s = stream.recv(4096)
            if len(s) == 0:
                break
            buf += s
            cmds = buf.split(sep)
            buf = cmds[-1]
            for i in cmds[:-1]:
                yield i
