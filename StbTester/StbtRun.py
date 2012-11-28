#!/usr/bin/env python
'''
Created on 31 Oct 2012

@author: YouView
'''

from Queue import Queue
from StbTester.apis.impls.original.MatchTimeout import MatchTimeout
from StbTester.core.utils.ArgParser import loadDefaultArgs
from StbTester.core.utils.SaveFrame import saveFrame
from StbTester.playback.TestRunner import TestRunner
from optparse import OptionParser
import glib
import gobject
import sys
import traceback

def parseArgs(args=sys.argv[1:]):
    parser = OptionParser(version=1, description='Run one or more Stb-Tester test scripts')
    defaults = loadDefaultArgs('run')
    #    Common options:
    parser.add_option('--source-pipeline',
                      action="store",
                      dest="source_pipeline",
                      type="str",
                      help='A gstreamer pipeline to use for A/V input (default: %(default)s)')
    parser.add_option('--sink-pipeline',
                      action="store",
                      dest="sink_pipeline",
                      type="str",
                      help='A gstreamer pipeline to use for video output (default: %(default)s)')
    parser.add_option('--debug-level',
                      action="store",
                      dest="debug_level",
                      type="int",
                      help='The debug level to use')
    parser.add_option("--control",
                      action="store",
                      dest="control",
                      default=None,
                      help='The remote control to control the stb (default: %(default)s)')
    #    Run specific options:
    parser.add_option("--script",
                      action="append",
                      dest="script",
                      default=[],
                      help='The script to execute')
    parser.add_option("--nose",
                      action="store_true",
                      dest="nose",
                      default=False,
                      help='Use Nose to discover test scripts')
    parser.add_option("--script-root",
                      action="store",
                      dest="script_root",
                      help='The root directory of the scripts (default: %(default)s) - available to the API')
    parser.add_option("--api-type",
                      action="store",
                      dest="api_type",
                      default="original",
                      help='The type of api used by the test script (default: %(default)s)')
    parser.add_option("--isolation",
                      action="store_true",
                      dest="isolation",
                      default=False,
                      help='Run each script in isolation (default: %(default)s)')
    parser.add_option("--disallow-builtins",
                      action="store_true",
                      default=False,
                      dest="disallow_builtins",
                      help='Allow python built-in methods when executing the script.')
    parser.add_option("--results_root",
                      action="store",
                      default=None,
                      dest="results_root",
                      help='Location to put results. Default is "None", ie: No results.')
    parser.set_defaults(**defaults)
    try:
        options, _args = parser.parse_args(args=args)
    except Exception, _e:
        traceback.print_exc()
        raise
    else:
        if options.disallow_builtins=="False":
            options.disallow_builtins = False
        elif options.disallow_builtins=="True":
            options.disallow_builtins = True
        return options

if __name__ == '__main__':
    mainLoop = glib.MainLoop()  #@UndefinedVariable
    gobject.threads_init()      #@UndefinedVariable
    args = parseArgs()
    count = 0
    while count<1:
        runner = TestRunner(args)
        runner.ignoreEvents(True)
        debugger = runner.debugger()
        runner.setup(mainLoop, Queue())
        try:
            runner.run(count)
        except MatchTimeout as e:
            traceback.print_exc()
            debugger.error("FAIL: %s: Didn't find match for '%s' after %d seconds."%(args.script, e.expected(), e.timeoutSecs()))
            screenshot = e.screenshot()
            if screenshot:
                saveFrame(e.screenshot(), "screenshot.png")
                debugger.debug("Saved screenshot to '%s'."%("screenshot.png"))
            sys.exit(1)
        finally:
            runner.teardown()
        count += 1
