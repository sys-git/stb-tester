#!/usr/bin/env python
'''
Created on 31 Oct 2012

@author: YouView
'''

from Queue import Queue
from StbTester.apis.ApiFactory import ApiFactory
from StbTester.apis.impls.common.errors.UITestFailure import UITestFailure
from StbTester.core.debugging.BreakpointAutoStepper import AutoStepper
from StbTester.core.utils.ArgFixer import ArgFixer
from StbTester.core.utils.ArgParser import loadDefaultArgs
from StbTester.playback.TVector import TVector
from StbTester.playback.TestPlayback import TestPlayback
from StbTester.playback.discovery.discovery import discover
from optparse import OptionParser
import glib
import gobject
import os
import sys
import traceback

def parseRunArgs(args=sys.argv[1:]):
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
    defaults["script"] = ArgFixer.fixAttr(defaults.get("script", []))
    defaults["library"] = ArgFixer.fixAttr(defaults.get("library", []))
    defaults["api_types"] = ArgFixer.fixAttr(defaults.get("api_types", []))
    parser.add_option("--script",
                      action="append",
                      dest="script",
                      help='The script to execute')
    parser.add_option("--nose",
                      action="store_true",
                      dest="nose",
                      help='Use Nose to discover test scripts')
    parser.add_option("--script-root",
                      action="store",
                      dest="script_root",
                      help='The root directory of the scripts (default: %(default)s) - available to the API')
    parser.add_option("--library",
                      action="append",
                      dest="library",
                      help='Append this directory to the sys-path prior to execution.')
    parser.add_option("--api-types",
                      action="append",
                      dest="api_types",
                      help='The type of apis to use by the test scripts (default: %(default)s)')
    parser.add_option("--isolation",
                      action="store_true",
                      dest="isolation",
                      help='Run each script in isolation (default: %(default)s)')
    parser.add_option("--disallow-builtins",
                      action="store_true",
                      dest="disallow_builtins",
                      help='Allow python built-in methods when executing the script.')
    parser.add_option("--auto-screenshot",
                      action="store_true",
                      dest="auto_screenshot",
                      help='Automatically take a screenshot on error.')
    parser.add_option("--results_root",
                      action="store",
                      dest="results_root",
                      help='Location to put results. Default is "None", ie: No results.')
    parser.set_defaults(**defaults)
    try:
        options, _args = parser.parse_args(args=args)
    except Exception, _e:
        traceback.print_exc()
        raise
    else:
        ArgFixer.fixBoolAttr(options, "disallow_builtins")
        ArgFixer.fixBoolAttr(options, "auto_screenshot")
        ArgFixer.fixBoolAttr(options, "nose")
        ArgFixer.fixBoolAttr(options, "isolation")
        ArgFixer.fixAttr(options.api_types)
        ArgFixer.fixAttr(options.library)
        ArgFixer.fixAttr(options.script)
        return options

def run():
    mainLoop = glib.MainLoop()  #@UndefinedVariable
    gobject.threads_init()      #@UndefinedVariable
    args = parseRunArgs()
    count = 0
    def wrapArgs(args):
        for index, script in enumerate(args.script):
            args.script[index] = TVector(filename=os.path.realpath(script), root=os.path.realpath(args.script_root))
    #    Now dynamically create the apis in the factory:
    ApiFactory.create(args.api_types)
    if args.nose==True:
        discover(args)
    if len(args.script_root)>0:
        sys.path.append(os.path.realpath(args.script_root))
    args.project_root = os.path.join(os.path.dirname(__file__), "..")
    error = 0
    #    Single iteration for now:
    while (count<1) and (error==0):
        terminate = False
        autoStepper = AutoStepper(lambda: (terminate!=0))
        runner = TestPlayback(args, notifier=autoStepper.func)
        debugger = runner.debugger()
        runner.setup(mainLoop, Queue())
        try:
            runner.run(count)
        except UITestFailure as e:
            debugger.error("FAIL: %(E)s."%{"E":str(e)})
            error = 1
        finally:
            terminate = True
            runner.teardown()
            autoStepper.kill()
        count += 1
    sys.exit(error)

if __name__ == '__main__':
    run()
