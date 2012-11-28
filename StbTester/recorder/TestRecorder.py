'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.core.utils.ArgvHider import ArgvHider
import shutil
with ArgvHider():
    import pygst  # gstreamer
    pygst.require("0.10")
    import gst
from StbTester.core.debugging.Debugger import Debugger
from StbTester.core.display.RecorderDisplay import RecorderDisplay
from StbTester.core.utils.PathUtils import mkdir
from StbTester.core.utils.SaveFrame import saveFrame
from StbTester.remotes.RemotePlaybackFactory import RemotePlaybackFactory
from StbTester.remotes.RemoteRecorderFactory import RemoteRecorderFactory
import itertools
import os

class TestRecorder(object):
    def __init__(self, args, script):
        self._args = args
        self._script = script
        self._outputDirname = os.path.dirname(args.output_file)
        self._debugger = Debugger(args.debug_level)
        self._display = RecorderDisplay(args.source_pipeline, args.sink_pipeline, self._debugger)
        self._setup()
    def debugger(self):
        return self._debugger
    def _setup(self):
        self._clearOutputDir()
        mkdir(self._outputDirname)
        try:
            self._fp = open(self._args.output_file, 'w')
        except IOError as e:
            e.strerror = "Failed to write to output-file '%s': %s"%(os.path.realpath(self._args.output_file), e.strerror)
            raise
        open(os.path.join(self._outputDirname, "__init__.py"), "w").write("'''\nAuto-generated test.\n'''")
    def teardown(self, failure=None):
        if failure and (self._args.cleanup_on_failure!=None):
            self._clearOutputDir()
    def _clearOutputDir(self):
        try:    shutil.rmtree(self._outputDirname)
        except: pass
    def record(self):
        try:
            self._record(
                         self._display,
                         RemoteRecorderFactory(self._args.control_recorder, self._debugger),
                         RemotePlaybackFactory(self._args.control, self._display, self._debugger),
                         self._fp,
                         self._outputDirname,
                         self._debugger,
                         )
        finally:
            try:    self._fp.close()
            except: pass
            self._debugger.debug("Script recording finished.")
    @staticmethod
    def _record(display, remoteInput, control, scriptOut, outputDirname, debugger):
        count = itertools.count()
        oldKey = None
        while True:
            interrupt = False
            try:
                key = remoteInput.next()
            except (KeyboardInterrupt, StopIteration):
                interrupt = True
            buf = display.getScreenshot().get_property('last-buffer')
            if not interrupt:
                control.press(key)
            if oldKey:
                filename = '%04d-%s-complete.png' % (count.next(), oldKey)
                saveFrame(buf, os.path.join(outputDirname, filename))
                scriptOut.write("wait_for_match('%s')\n" % filename)
            if interrupt:
                return
            scriptOut.write("press('%s')\n" % key)
            oldKey = key
