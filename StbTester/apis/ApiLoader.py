'''
Created on 4 Dec 2012

@author: francis
'''

from StbTester.apis.ApiHelper import ApiHelper
from StbTester.core.debugging.BreakpointStepper import BreakpointStepper
from StbTester.core.errors.DuplicateApiNamespaceError import \
    DuplicateApiNamespaceError
from StbTester.core.namespace.NamespaceWrapperController import \
    NamespaceWrapperController
from StbTester.core.namespace.notifications.api.ApiLoad import ApiLoad
from StbTester.core.namespace.notifications.breakpoints.PostApiManipulationBreakpoint import \
    PostApiManipulationBreakpoint
from StbTester.core.namespace.notifications.breakpoints.PreApiManipulationBreakpoint import \
    PreApiManipulationBreakpoint
from StbTester.playback.commands.RunnerCommand import Command
from StbTester.playback.commands.TRCommands import TRCommands
from sets import Set
import inspect
import time

class ApiLoader(object):
    def __init__(self, apiComparitor, namespace, apiInstances, srcPath, control,
                 display, debugger, namespaceWrapperControllers, getWaitOnEvent,
                 projectRoot, event,
                 q=None, uId=None, scriptName=None):
        self._comparitor = apiComparitor
        self._namespace = namespace
        self._apiInstances = apiInstances
        self._srcPath = srcPath
        self._control = control
        self._display = display
        self._debugger = debugger
        self._namespaceWrapperControllers = namespaceWrapperControllers
        self._getWaitOnEvent = getWaitOnEvent
        self._projectRoot = projectRoot
        self._event = event
        self._q = q
        self._uId = uId
        self._scriptName = scriptName
    def injects(self, what, mode=0):
        r"""
        @summary: Called by the test script to inject an api into another
        api's namespace.
        @attention: Not strictly necessary because it's a subset of __loads__().
        @param whats: list or single string representing the new namespace(s).
        @param param: mode = 0  (blat existing namespace methods of same name and replace with new ones)
                      mode = 1  (update only namespace methods of different name)
        """
        if (mode!=0) and (mode!=1):
            mode = -2
        msg = "__injects__ called: '%(W)s', mode: '%(M)s'"%{"M":mode, "W":what}
        if self._debugger==None:
            print msg
        else:
            self._debugger.debug(msg)
        return self._load(TRCommands.API_LOAD, what, mode=mode)
    def __call__(self, whats, mode=2):
        r"""
        @summary: Load the namespaces defined as normal in whats into our
        namespace.
        @attention: This does not affect the ApiFactory._map
        @attention: ONLY to be called directly from a test.
        @see: _load().
        """
        msg = "__loads__ called: '%(W)s', mode: '%(M)s'"%{"M":mode, "W":whats}
        if self._debugger==None:
            print msg
        else:
            self._debugger.debug(msg)
        return self._load(TRCommands.API_LOAD, whats, mode=mode)
    def _load(self, cmd, whats, mode=-2):
        r"""
        @param param: mode not in [-1, 0, 1, 2] Raise an error if namespace already exists.
                      mode = -1 Blat (replace existing namespace (if exists) with new one).
                      mode = 0  Freshen (blat existing namespace methods of same name and replace with new ones)
                      mode = 1  Update (update only namespace methods of different name)
                      mode = 2  Load (do nothing if apid is already loaded with the same namespace)
        """
        if not isinstance(whats, list):
            whats = [whats]
        callers = inspect.stack()
        frame = callers[2]
        filename = frame[1]
        lineNumber = frame[2]
        #    Now attempt to load the namespaces:
        def doLoad():
            for what in whats:
                result = None
                apid = ApiHelper.loadApiType(what, apids=self._comparitor.apids, root=self._projectRoot)
                try:
                    api = apid.api()
                    NS = apid.ns()
                    alreadyLoadedInSameNamespace = True
                    found = True
                    try:
                        if NS in self._namespaceWrapperControllers.keys():
                            raise DuplicateApiNamespaceError([(NS, apid.apiType())])
                        if NS in self._apiInstances.keys():
                            raise DuplicateApiNamespaceError([(NS, apid.apiType())])
                        if NS in self._namespace["__builtins__"].keys():
                            raise DuplicateApiNamespaceError([(NS, apid.apiType())])
                    except DuplicateApiNamespaceError, _e:
                        #    Duplicate found, however is the apid the same?
                        alreadyLoadedInSameNamespace = False
                        for apid_ in self._comparitor.apids:
                            if apid==apid_:
                                #    Yes, no error, do nothing - module already loaded!
                                alreadyLoadedInSameNamespace = True
                                break
                        if alreadyLoadedInSameNamespace==False:
                            #    Another api is using the same namespace.
                            if mode==-1:
                                #    Should auto-blat with new namespace!
                                found = True
                            elif mode==2:
                                #    Api already loaded with same namespace.
                                found = False
                            elif mode==0:
                                #    Should auto-blat!
                                self._freshenNamespace(api, apid)
                                self._debugger.debug("API: Freshened '%(NS)s' from '%(W)s'"%{"NS":NS, "W":what})
                                continue
                            elif mode==1:
                                #    Determine new methods and inject them using the NamespaceWrapperController:
                                self._updateNamespace(api, apid)
                                self._debugger.debug("API: Updated '%(NS)s' from '%(W)s'"%{"NS":NS, "W":what})
                                continue
                            else:
                                raise
                        else:
                            #    Same api is using the same namespace.
                            found = False
                    if found==True:
                        theApi = api(self._control, self._display, self._srcPath, self._debugger)
                        self._apiInstances[NS] = theApi
                        self._namespaceWrapperControllers[NS] = NamespaceWrapperController.create(apid, theApi.namespace(), waitOnEvent=self._getWaitOnEvent, debugger=self._debugger)
                        wrapper = self._namespaceWrapperControllers[NS].getWrapper()
                        self._comparitor.apids.append(apid)
                        self._namespace["__builtins__"][NS] = wrapper
                        self._debugger.debug("API: Loaded '%(NS)s' from '%(W)s'"%{"NS":NS, "W":what})
                    else:
                        self._debugger.debug("API: Already loaded '%(NS)s' from '%(W)s'"%{"NS":NS, "W":what})
                except Exception, result:
                    raise
                finally:
                    if self._q!=None:
                        self._q.put(Command(cmd, self._uId, data=ApiLoad(self._scriptName, time.time(), what, apid, result, callers[2:], filename, lineNumber, mode=mode)))

        def getPreNotifier(timeStart, frames, filename, lineNumber):
            return PreApiManipulationBreakpoint(whats, mode, timeStart, frames, filename, lineNumber)
        def getPostNotifier(timeStart, frames, filename, lineNumber, timeEnd, result, isErr):
            return PostApiManipulationBreakpoint(whats, mode, timeStart, frames, filename, lineNumber, timeEnd, result, isErr)
        BreakpointStepper(
                          self._event,
                          lambda: None,
                          self._debugger,
                          "Api::__load__, mode: '%(M)s': '%(A)s'."%{"M":mode, "A":whats},
                          doLoad,
                          callers[2:],
                          getPreNotifier,
                          getPostNotifier,
                          waitOnEvent=self._getWaitOnEvent,
                         )
    def _freshenNamespace(self, api, apid):
        r"""
        @summary: Freshen (blat existing namespace methods of same name and replace with new ones)
        """
        NS = apid.ns()
        enswc = self._namespaceWrapperControllers[NS]
        theApi = api(self._control, self._display, self._srcPath, self._debugger)
        nNamespace = theApi.namespace()
        eNamespace = enswc.getWrapper().namespace()
        #    Find the new keys:
        eKeys = Set(eNamespace.keys())
        nKeys = Set(nNamespace.keys())
        sameKeys = nKeys & eKeys
        namespace = {}
        for key in sameKeys:
            namespace[key] = nNamespace[key]
        #    Inject the new namespace 
        return enswc.overwriteApi(namespace)
    def _updateNamespace(self, api, apid):
        r"""
        @summary: Update (update only namespace methods of different name)
        """
        NS = apid.ns()
        enswc = self._namespaceWrapperControllers[NS]
        theApi = api(self._control, self._display, self._srcPath, self._debugger)
        nNamespace = theApi.namespace()
        eNamespace = self._apiInstances[NS].namespace()
        #    Find the new keys:
        eKeys = Set(eNamespace.keys())
        nKeys = Set(nNamespace.keys())
        deltaKeys = nKeys - eKeys
        namespace = {}
        for key in deltaKeys:
            namespace[key] = nNamespace[key]
        #    Inject the new namespace 
        return enswc.insertApi(namespace)

