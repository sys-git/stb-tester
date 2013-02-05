'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.apis.ApiFactory import ApiFactory
from StbTester.apis.impls.common.BaseApi import BaseApi
from StbTester.apis.impls.common.errors.UINoseTestError import UINoseTestError
from StbTester.apis.impls.common.errors.UINoseTestFailure import \
    UINoseTestFailure
from StbTester.apis.impls.common.errors.UITestError import UITestError
from StbTester.apis.impls.original.MatchTimeout import MatchTimeout
from StbTester.core.debugging.Debugger import Debugger
from StbTester.core.display.PlaybackDisplay import PlaybackDisplay
from StbTester.core.errors.UiError import UiError
from StbTester.core.namespace.NamespaceWrapperController import \
    NamespaceWrapperController
from StbTester.core.utils.PathUtils import mkdir
from StbTester.core.utils.SaveFrame import saveScreenShot
from StbTester.core.utils.TimeUtils import truncateInteger
from StbTester.playback.TVector import TVector
from StbTester.playback.commands.RunnerCommand import Command
from StbTester.playback.commands.TRCommands import TRCommands
from StbTester.playback.discovery.discovery import discover
from StbTester.playback.results.NoResult import NoResult
from StbTester.playback.results.Result import Result
from StbTester.remotes.RemotePlaybackFactory import RemotePlaybackFactory
from xml.sax.saxutils import quoteattr
import copy
import nose
import os
import tempfile
import time
import traceback
import xml.dom.minidom
#import shutil

class StbtTestRunner(object):
    def __init__(self, args, getWindowId=None, waitOnEvent=None, notifier=None, ignoreEvents=True):
        self._args = args
        self._api = None
        self._apiInstance = None
        self._notifier = notifier
        self._getWindowId = getWindowId
        self._results = {}
        if waitOnEvent==None:
            def doWaitOnEvent():
                return False
            waitOnEvent = doWaitOnEvent
        self.__waitOnEvent = waitOnEvent
        self._namespaceWrapperController = None
        self._debugger = Debugger(args.debug_level)
        self._debugger.debug("Arguments:\n"+"\n".join(["%s: %s" % (k, v) for k, v in args.__dict__.items()]))
        self._resultsDir = None
        self._ignoreEvents = ignoreEvents
        self._createResultsDir()
        for index, script in enumerate(args.script):
            if isinstance(script, basestring):
                args.script[index] = TVector(filename=os.path.realpath(script), root=os.path.realpath(args.script_root))
        discover(self._args)
    def getResultsDir(self):
        return self._resultsDir
    def _createResultsDir(self):
        p = self._args.results_root
        self._resultsDir = p
        if p!=None:
            path = os.path.realpath(p)
#            try:
#                shutil.rmtree(path)
#            except Exception, _e:
#                pass
            mkdir(path)
    def getNamespaceController(self):
        return self._namespaceWrapperController
    def ignoreEvents(self, enabler=True):
        self._ignoreEvents = enabler
    def getResults(self):
        return copy.deepcopy(self._results)
    def setup(self, mainLoop, q):
        self._display = PlaybackDisplay(self._args.source_pipeline, self._args.sink_pipeline, self._debugger, mainLoop, self._getWindowId)
        self._control = RemotePlaybackFactory(self._args.control, self._display, self._debugger)
        self._q = q
    def teardown(self):
        try:    self._apiInstance.abort()
        except: pass
        else:   time.sleep(1)
        self._control.teardown()
        self._display.teardown()
    def run(self, uId):
        namespace = None
        try:
            for scriptName in self._args.script:
                if self._args.isolation==True:
                    try:    del __builtins__["api"]
                    except: pass
                    self._doRun(scriptName, namespace, uId)
                else:
                    namespace = self._doRun(scriptName, namespace, uId)
        finally:
            try:    del __builtins__["api"]
            except: pass
    def _doRun(self, scriptName, namespace, uId):
        scriptRoot = self._args.script_root
        rFilename = StbtTestRunner._getExportFilename(scriptRoot, scriptName, self._resultsDir, self._debugger)
        try:
            self._run(scriptName, namespace, uId, rFilename)
        except UiError, e:
            e.setScriptName(scriptName)
            e.setResultName(rFilename)
            if self._args.auto_screenshot==True:
                if hasattr(e, "screenshot"):
                    screenshot = e.screenshot()
                    if screenshot:
                        path = saveScreenShot(screenshot, e.resultName(), "screenshot.png")
                        self._debugger.debug("Saved screenshot to '%(P)s'."%{"P":path})
            raise
    def _create(self, scriptName, namespace={}):
        srcPath = os.path.dirname(scriptName)
        #    Create the test API:
        self._setApi(self._createApi(self._args.api_type))
        #    Create the api instance:
        self._apiInstance = self._api(self._control,
                                      self._display,
                                      srcPath,
                                      self._debugger)
        #    Create the namespace:
        return self._createNamespace(self._args,
                                     scriptName,
                                     self._apiInstance,
                                     self._getWaitOnEvent,
                                     namespace=namespace,
                                     notifier=self._notifier,
                                     ignoreEvents=self._ignoreEvents,
                                     )
    def _run(self, scriptName, namespace, uId, rFilename):
        self._q.put(Command(TRCommands.RUNNING_START, uId, scriptName))
        key = scriptName
        self._results[key] = NoResult()
        timeStart = time.time()
        trace = None
        filename = scriptName.filename()
        try:
            if namespace==None:
                (namespace, self._namespaceWrapperController) = self._create(scriptName.filename())
            scriptRoot = self._args.script_root
            #    Execute the top-level script (and all downstream scripts) in this namespace.
            if self._args.nose==True:
                defaultTest = str(scriptName)
                oldDir = os.getcwd()
                os.chdir(scriptRoot)
                try:
                    #    Set the builtins api namespace so that the nose tests can see it:
                    for what in         ["api", "__file__", "__name__", "__srcdir__", "__script_root__"]:
                        __builtins__[what] = namespace["__builtins__"][what]
                    result = nose.run(argv=["hello.world.py",
                                            "--with-xunit",
                                            "--xunit-file=%(F)s"%{"F":rFilename},
                                            "--nocapture",
                                            "--nologcapture"],
                                      defaultTest=defaultTest)
                    #    Now check the xml file for the result:
                    self._checkResult(rFilename, self._debugger)
                finally:
                    os.chdir(oldDir)
            else:
                execfile(filename, namespace)
        except MatchTimeout, result:
            result.setScriptName(filename)
            self._debugger.debug(str(result))
            trace = traceback.format_exc()
            raise
        except RuntimeError, e:
            result = e
            self._debugger.error("Script RuntimeError raised: %(E)s\n%(T)s"%{"E":result, "T":traceback.format_exc()})
            trace = traceback.format_exc()
            raise
        except Exception, e:
            result = e
            self._debugger.error("Script execution raised: %(E)s\n%(T)s"%{"E":result, "T":traceback.format_exc()})
            trace = traceback.format_exc()
            raise
        else:
            self._debugger.debug("Script execution ok: %(N)s"%{"N":scriptName})
            result = Result.OK
        finally:
            timeEnd = time.time()
            duration = (timeEnd-timeStart)
            self._results[key] = Result(result)
            self._debugger.debug("Script execution finished: %(N)s"%{"N":scriptName})
            try:
                self._q.put(Command(TRCommands.RUNNING_FINISHED, uId, (scriptName, self._results[key])))
            except Exception, _e:
                pass
            #    Generate xUnit compatible XML result file:
            if self._args.nose==False:
                self._exportResult(rFilename, trace, duration, self._args.script_root, scriptName, namespace, self._results[key], self._debugger, self._resultsDir)
        return namespace
    @staticmethod
    def _checkResult(filename, debugger):
        StbtTestRunner._searchForErrorCases(open(filename, "r").read(), debugger)
    @staticmethod
    def _searchForErrorCases(x, debugger):
        try:
            dom=xml.dom.minidom.parseString(unicode(x.encode("utf-8"), "utf-8").encode("utf-8"))
            el=dom.firstChild
            error=el.getAttribute("errors")
            errCount=int(error)
            failure=el.getAttribute("failures")
            failCount=int(failure)
            if (errCount>0) or (failCount>0):
                el1=dom.firstChild
                el1=el1.firstChild
                el1=el1.firstChild
                type_ = el1.getAttribute("type")
                message = el1.getAttribute("message")
                msg = " ".join([type_, message])
                if errCount>0:
                    raise UINoseTestError(msg)
                else:
                    raise UINoseTestFailure(msg)
        except UITestError:
            raise
        except Exception, _e:
            debugger.error("Error parsing XML using minidom!")
            raise UITestError("Failed to parse xml: <%(X)s>"%{"X":x})
    @staticmethod
    def _getExportFilename(scriptRoot, scriptName, resultsDir, debugger):
        path = os.path.realpath(scriptRoot)+os.sep
        fname = os.path.realpath(scriptName.filename())
        _, _, fname = fname.partition(path)
        module = ".".join(fname.split(os.sep))
        moduleNameNoClass = os.path.splitext(os.path.basename(module))[0]
        moduleName = moduleNameNoClass+".xml"
        filename = os.path.realpath(os.path.join(resultsDir, moduleName))
        if os.path.exists(filename):
            fd, tFilename = tempfile.mkstemp(prefix=module, suffix=".xml", dir=resultsDir)
            os.close(fd)
            debugger.error("Test path already exists, results written to: %(F)s"%{"F":tFilename})
            filename = tFilename
        return filename
    @staticmethod
    def _exportResult(rFilename, trace, duration, scriptRoot, scriptName, namespace, result, debugger, resultsDir):
        try:
            path = os.path.realpath(scriptRoot)+os.sep
            fname = os.path.realpath(scriptName.filename())
            _, _, fname = fname.partition(path)
            module = ".".join(fname.split(os.sep))
            timeDuration = truncateInteger(duration, 2)
            s = ['<?xml version="1.0" encoding="UTF-8"?>']
            errorCount = 0
            failureCount = 0
            skipCount = 0
            totalCount = 1
            message = "no message !"
            errorType = "no.error.type"
            if result==None:
                skipCount = 1
            elif isinstance(result, NoResult):
                errorCount = 1
                message = "Test initiated but not started"
                trace = "Nothing to show here."
            elif isinstance(result, Result):
                actualResult = result.result()
                if isinstance(actualResult, Exception):
                    if isinstance(actualResult, UITestError):
                        errorCount = 1
                    else:
                        failureCount = 1
                    message = trace.splitlines()[-1]
                    errorType1 = str(type(actualResult))
                    _, _, errorType = errorType1.partition("'")
                    errorType = errorType.rstrip("'>")
            moduleNameNoClass = os.path.splitext(os.path.basename(module))[0]
            moduleName = moduleNameNoClass+".xml"
            filename = os.path.realpath(os.path.join(resultsDir, moduleName))
            args = {"E":errorCount, "F":failureCount, "S":skipCount, "T":totalCount}
            s.append('<testsuite name="StbTester" tests="%(T)s" errors="%(E)s" failures="%(F)s" skip="%(S)s">'%args)
            if trace!=None:
                trace = quoteattr(trace)
            s.append('<testcase classname="%(M)s" name="test" time="%(D)s">'%{"M":moduleNameNoClass, "D":timeDuration})
            if failureCount!=0:
                s.append('<failure type="%(T)s" message="%(M)s">'%{"M":message, "T":errorType})
                s.append('<![CDATA[%(T)s'%{"T":trace})
                s.append(']]></failure>')
            elif errorCount!=0:
                s.append('<error type="%(T)s" message="%(M)s">'%{"M":message, "T":errorType})
                s.append('<![CDATA[%(T)s'%{"T":trace})
                s.append(']]></error')
            s.append('</testcase>')
            s.append('</testsuite>')
            contents = "\n".join(s)
            if os.path.exists(filename):
                fd, tFilename = tempfile.mkstemp(prefix=module, suffix=".xml", dir=resultsDir)
                os.close(fd)
                debugger.error("Test path already exists, results written to: %(F)s"%{"F":tFilename})
                filename = tFilename
            open(filename, "w").write(contents)
            debugger.debug("Results for <%(T)s> written to: <%(R)s>"%{"T":scriptName, "R":filename})
        except Exception, _e:
            debugger.error("Failed to export result because:\n%(T)s"%{"T":traceback.format_exc()})
        else:
            return filename
    @staticmethod
    def _createNamespace(args, scriptName, api, getWaitOnEvent, namespace={}, notifier=None, ignoreEvents=False):
        srcPath = os.path.dirname(scriptName)
        if args.disallow_builtins==True:
            namespace["__builtins__"] = {}
        else:
            namespace["__builtins__"] = __builtins__
        if "api" in __builtins__:
            assert isinstance(api, BaseApi)
        namespaceWrapperController = NamespaceWrapperController.create(api.namespace(), waitOnEvent=getWaitOnEvent)
        namespaceWrapperController.getWrapper().ignoreEvents(ignoreEvents)
        if notifier!=None:
            notifier(namespaceWrapperController.getEventNotifiers())
        wrapper = namespaceWrapperController.getWrapper()
        namespace["__builtins__"]["api"] = wrapper
        namespace["__builtins__"]["__file__"] = scriptName
        namespace["__builtins__"]["__name__"] = "__main__"  #    override, allows top-level script to execute.
        namespace["__builtins__"]["__srcdir__"] = srcPath
        namespace["__builtins__"]["__script_root__"] = args.script_root
        return (namespace, namespaceWrapperController)
    def _setApi(self, api):
        self._api = api
    @staticmethod
    def _createApi(apiType):
        return ApiFactory(apiType)
    def debugger(self):
        return self._debugger
    def _getWaitOnEvent(self):
        return self.__waitOnEvent()
