'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.core.errors.ConfigurationError import ConfigurationError
from StbTester.remotes.impls.irnetbox.IRNetBoxRemote import IRNetBoxRemote
from StbTester.remotes.impls.lirc.LircRemote import LircRemote
from StbTester.remotes.impls.null.NullRemote import NullRemote
from StbTester.remotes.impls.test.TestRemote import TestRemote
from StbTester.remotes.impls.virtual.VirtualRemote import VirtualRemote
import re

class RemotePlaybackFactory(object):
    @staticmethod
    def __new__(cls, uri, display, debugger):
        if uri.lower() == 'none':
            return NullRemote()
        if uri.lower() == 'test':
            return TestRemote(display, debugger)
        vr = re.match(r'vr:(?P<hostname>[^:]*)(:(?P<port>\d+))?', uri)
        if vr:
            d = vr.groupdict()
            return VirtualRemote(d['hostname'], int(d['port'] or 2033), debugger)
        lirc = re.match(r'lirc:(?P<lircd_socket>[^:]*):(?P<control_name>.*)', uri)
        if lirc:
            d = lirc.groupdict()
            return LircRemote(d['lircd_socket'] or '/var/run/lirc/lircd',
                              d['control_name'],
                              debugger)
        irnb = re.match(
            r'irnetbox:(?P<hostname>[^:]+):(?P<output>\d+):(?P<config>.+)', uri)
        if irnb:
            d = irnb.groupdict()
            return IRNetBoxRemote(d['hostname'], d['output'], d['config'], debugger)
        raise ConfigurationError('Invalid remote control URI: "%s"'%uri)
