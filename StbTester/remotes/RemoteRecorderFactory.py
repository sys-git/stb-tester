'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.core.errors.ConfigurationError import ConfigurationError
from StbTester.remotes.impls.file.FileRemote import FileRemote
from StbTester.remotes.impls.lirc.LircRemote import LircRemote
from StbTester.remotes.impls.virtual.VirtualRemote import VirtualRemote
import re

class RemoteRecorderFactory(object):
    @staticmethod
    def __new__(cls, uri, debugger):
        vr = re.match(r'vr:(?P<hostname>[^:]*)(:(?P<port>\d+))?', uri)
        if vr:
            d = vr.groupdict()
            return VirtualRemote.listen(d['hostname'], int(d['port'] or 2033), debugger)
        lirc = re.match(r'lirc:(?P<lircd_socket>[^:]*):(?P<control_name>.*)', uri)
        if lirc:
            d = lirc.groupdict()
            return LircRemote.listen(d['lircd_socket'] or '/var/run/lirc/lircd',
                                      d['control_name'],
                                      debugger)
        f = re.match('file://(?P<filename>.+)', uri)
        if f:
            return FileRemote.listen(f.group('filename'), debugger)
        raise ConfigurationError('Invalid remote control recorder URI: "%s"' % uri)
