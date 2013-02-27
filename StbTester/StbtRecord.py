#!/usr/bin/env python
'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.core.utils.ArgParser import loadDefaultArgs
from StbTester.recorder.TestRecorder import TestRecorder
from optparse import OptionParser
import sys
import traceback

def parseRecordArgs(args=sys.argv[1:]):
    parser = OptionParser(version=1, description='Create a single Stb-Tester test script')
    defaults = loadDefaultArgs('record')
    #    Common options:
    parser.add_option('--source-pipeline',
                      action="store",
                      dest="source_pipeline",
                      type="str",
                      help='A gstreamer pipeline to use for A/V input (default: %(default)s).')
    parser.add_option('--sink-pipeline',
                      action="store",
                      dest="sink_pipeline",
                      type="str",
                      help='A gstreamer pipeline to use for video output (default: %(default)s).')
    parser.add_option('--debug-level',
                      action="store",
                      dest="debug_level",
                      type="int",
                      help='The debug level to use.')
    parser.add_option("--control",
                      action="store",
                      dest="control",
                      default=None,
                      help='The remote control to control the stb (default: %(default)s).')
    #    Record specific options:
    parser.add_option("--output-file",
                      action="store",
                      dest="output_file",
                      help='The output script file to write.')
    parser.add_option("--control-recorder",
                      action="store",
                      dest="control_recorder",
                      help='The control to use for the recordings.')
    parser.add_option("--cleanup-on-failure",
                      action="store_true",
                      dest="cleanup_on_failure",
                      default=False,
                      help='Cleanup output directory if recording fails.')
    parser.set_defaults(**defaults)
    try:
        options, args = parser.parse_args(args=args)
    except Exception, _e:
        traceback.print_exc()
    return options, args

def record():
    (args, script) = parseRecordArgs()
    recorder = TestRecorder(args, script)
    debugger = recorder.debugger()
    try:
        recorder.record()
        failure = None
    except Exception, failure:
        debugger.error("FAIL: Recording incomplete!")
        sys.exit(1)
    finally:
        recorder.teardown(failure)

if __name__ == '__main__':
    record()
