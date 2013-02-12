'''
Created on 31 Oct 2012

@author: YouView
'''

import re
import socket

def FakeLircd(address):
    # This needs to accept 2 connections (from LircRemote and
    # lirc_remote_listen) and, on receiving input from the LircRemote
    # connection, write to the lirc_remote_listen connection.
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(address)
    s.listen(5)
    listener, _ = s.accept()
    control, _ = s.accept()
    for cmd in control.makefile():
        m = re.match(r'SEND_ONCE (?P<control>\w+) (?P<key>\w+)', cmd)
        if m:
            d = m.groupdict()
            listener.sendall('00000000 0 %s %s\n' % (d['key'], d['control']))
