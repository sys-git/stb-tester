'''
Created on 5 Nov 2012

@author: francis
'''

import pygst # gstreamer
from StbTester.core.namespace.notifications.api.ApiRequires import ApiRequires
pygst.require("0.10")
import gst

from PyQt4 import uic, QtCore, Qt, QtGui
from PyQt4.Qsci import QsciScintilla, QsciLexerPython
from PyQt4.QtCore import SIGNAL, SLOT
from PyQt4.QtGui import QApplication, QMainWindow
from Queue import Empty
from StbTester.StbtRun import parseArgs
from StbTester.apis.ApiFactory import ApiFactory
from StbTester.apis.impls.common.errors.UITestFailure import UITestFailure
from StbTester.core.debugging.Debugger import Debugger
from StbTester.core.events.Events import Events
from StbTester.core.namespace.notifications.BaseNotification import \
    BaseNotification
from StbTester.core.namespace.notifications.api.BaseApiNotification import \
    BaseApiNotification
from StbTester.core.namespace.notifications.breakpoints.CallBreakpoint import \
    CallBreakpoint
from StbTester.core.namespace.notifications.breakpoints.ManipulationBreakpoint import \
    ManipulationBreakpoint
from StbTester.core.namespace.notifications.breakpoints.PostBreakpoint import \
    PostBreakpoint
from StbTester.core.namespace.notifications.breakpoints.PreApiCallBreakpoint import \
    PreApiCallBreakpoint
from StbTester.core.namespace.notifications.breakpoints.PreBreakpoint import \
    PreBreakpoint
from StbTester.core.utils.SaveFrame import saveFrame
from StbTester.core.utils.TimeUtils import timestamp
from StbTester.playback.TVector import TVector
from StbTester.playback.TestPlayback import TestPlayback
from StbTester.playback.commands.RunnerCommand import Command
from StbTester.playback.commands.TRCommands import TRCommands
from StbTester.playback.discovery.discovery import discover
from multiprocessing.synchronize import Semaphore, RLock
import Queue
import copy
import glib
import gobject
import itertools
import os
import sys
import threading
import traceback

testingDebugLevel = 1

class SubContext(object):
    def __init__(self, uId):
        self._uId = uId
        self._runner = None         #    The thread that works the testRunner's thread.
        self._testRunner = None     #    Does the work
        self._stepListener = None
        self._runnerEnabled = False
        self._runnerStepListener = None
        self._q = Queue.Queue()
        self._lock = RLock()
    def __enter__(self, *args, **kwargs):
        self._lock.acquire()
        return self
    def __exit__(self, *args, **kwargs):
        self._lock.release()
    def put(self, cmd, data=None):
        with self._lock:
            if self._runner!=None and self._q:
                self._q.put(Command(cmd, self._uId, data))
    def __str__(self):
        return "SubContext[%(U)s]"%{"U":self._uId}

class Context(object):
    _uId = itertools.count(0)
    def __init__(self, uId=None):
        self._uId = uId
        self._lock = RLock()
        self._ctx = {}      #    {uId:SubContext}
    def __enter__(self, *args, **kwargs):
        self._lock.acquire()
        return self
    def __exit__(self, *args, **kwargs):
        self._lock.release()
    def new(self):
        uId = Context._uId.next()
        sctx = SubContext(uId)
        with self._lock:
            self._ctx[uId] = sctx
            #    The 'current' SubContext is now the new one:
            self._uId = uId
        return sctx
    def __call__(self, uId=None):
        with self._lock:
            if uId==None:
                uId = self._uId
            if uId in self._ctx.keys():
                return self._ctx[uId]
    def put(self, cmd, uId=None, data=None):
        with self._lock:
            sctx = self(uId)
            if sctx:
                sctx.put(cmd, data=data)
    def __str__(self):
        return "Context[%(U)s]"%{"U":self._uId}
    def destroy(self, uId):
        with self._lock:
            sctx = self(uId)
            if sctx:
                if sctx._testRunner!=None:
                    #    Nothing we can do can interrupt this thread!
                    sctx._testRunner = None
                sctx._q = None
                if sctx._runner!=None:
                    sctx._runner.join()
                    sctx._runner = None
                del self._ctx[uId]

class QtStbtRun(QMainWindow):
    ICON_LOC_APP = "app_icon.png"
    def __init__(self, args, mainLoop, resourcePath):
        QMainWindow.__init__(self)
        self._args = args
        self._resourcePath = resourcePath
        self._scripts = None
        self._events = Events()
        self._mainLoop = mainLoop
        self._settings = QtCore.QSettings()
        self._settings.setPath(Qt.QSettings.IniFormat, Qt.QSettings.UserScope, "YouView-StbTester-Runner")
        self._events("APP-OPEN")
    def closeEvent(self, event):
        self._events("APP-CLOSE")
        if (self._scripts.close()==False):  # or (self._editor.close()==False):
            event.ignore()
            return
        self._events.dump()
        self._saveUi()
        event.accept()
    def _saveUi(self, settings=None):
        if settings==None:
            settings = self._settings
        settings.beginGroup("ui")
        settings.remove("")
        size = self.size()
        pos = self.pos()
        print "size: %(W)s  x %(H)s"%{"W":size.width(), "H":size.height()}
        print "pos: %(X)s, %(Y)s"%{"X":pos.x(), "Y":pos.y()}
        try:
            settings.setValue("size", size)
            settings.setValue("pos", pos)
            self._scripts.saveUi()
            self._codeFollower.saveUi()
        finally:
            settings.endGroup()
            settings.sync()
    def _loadUi(self, settings=None):
        if settings==None:
            settings = self._settings
        settings.beginGroup("ui")
        try:
            size = settings.value("size", defaultValue=QtCore.QSize(870, 762)).toSize()
            pos = settings.value("pos", QtCore.QPoint(0, 0)).toPoint()
            self.move(pos)
            self.resize(size)
            self._scripts.loadUi()
        finally:
            settings.endGroup()
    def show(self):
        super(QtStbtRun, self).show()
        self._appIcon = QtGui.QIcon(QtGui.QPixmap(os.path.join(self._resourcePath, "icons", QtStbtRun.ICON_LOC_APP)))
        self.setWindowIcon(self._appIcon)
        self.setWindowTitle('Video-Player')
        self._scripts = Scripts(self)
        uic.loadUi(os.path.join(self._resourcePath, self._scripts.RESOURCE_NAME), self._scripts)
        self._codeFollower = CodeFollower(self)
        uic.loadUi(os.path.join(self._resourcePath, self._codeFollower.RESOURCE_NAME), self._codeFollower)
        self.connect(self.action_exit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'), QtCore.Qt.QueuedConnection)
        self._scripts.show()
        self._codeFollower.show()
        self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        self.splitter1.addWidget(self._scripts)
        self.splitter1.addWidget(self._codeFollower)
        self.splitter1.setOpaqueResize(False)
        self.setCentralWidget(self.splitter1)
        self.splitter1.show()
        self._loadUi()

class CodeFollower(QtGui.QFrame):
    RESOURCE_NAME = "CodeFollower.ui"
    ARROW_MARKER_NUM = 8
    def __init__(self, parent):
        super(CodeFollower, self).__init__(parent=parent)
        self._parent = parent
        self._settings = parent._settings
        self._filename = ""
        self._lineNumber = 0
    def show(self):
        self.textEdit = QsciScintilla(self.frame_editor)
        self.textEdit.setReadOnly(True)
        configureQScintilla(self.textEdit, self.frame_editor)
        self.textEdit.markerDefine(QsciScintilla.RightArrow, self.ARROW_MARKER_NUM)
        self.textEdit.setCaretLineBackgroundColor(QtGui.QColor(0, 200, 0))
        self.textEdit.setMarginSensitivity(1, True)
        super(CodeFollower, self).show()
        self.connect(self._parent, Qt.SIGNAL("followCode(PyQt_PyObject)"), self._followCode)
        self.connect(self._parent, Qt.SIGNAL("apiExecuting()"), self._onApiExecuting)
        self.connect(self._parent, Qt.SIGNAL("runnerFinished(int)"), self._onRunnerFinished, QtCore.Qt.QueuedConnection)
        filename = self._parent._args.script[0].filename()
        self.textEdit.setText((open(filename, "r").read()))
        self.lineEdit_TestScriptName.setText(filename)
    def saveUi(self, settings=None):
        if settings==None:
            settings = self._settings
        settings.beginGroup("CodeFollower")
        settings.remove("")
        try:
            pass
        finally:
            settings.endGroup()
            settings.sync()
    def loadUi(self, settings=None):
        if settings==None:
            settings = self._settings
        settings.beginGroup("CodeFollower")
        try:
            pass
        finally:
            settings.endGroup()
    def resizeEvent(self, event):
        newSize = event.size()
        targetSize = QtCore.QSize(newSize.width()-25, newSize.height()-105)
        self.textEdit.resize(targetSize)
    def _onApiExecuting(self):
        colour = QtGui.QColor("#ff7e00")
        self._addMarker(colour, self.ARROW_MARKER_NUM)
    def _followCode(self, data):
        filename = data.filename()
        self._lineNumber = lineNumber = data.lineNumber()
        if filename!=self._filename:
            self.textEdit.setText((open(filename, "r").read()))
        self._prepMarker(lineNumber)
        self._filename = filename
        if isinstance(data, PostBreakpoint):
            if data.isErr():
                colour = QtGui.QColor("#ee1111")
            else:
                colour = QtGui.QColor("#11ee11")
        elif isinstance(data, PreBreakpoint):
            colour = QtGui.QColor("#11ffff")
        else:
            raise Exception("UNKNOWN DATA RECEIVED: <%(D)s>."%{"D":data})
        self._addMarker(colour, lineNumber=lineNumber)
        self._updateStack(data)
    def _updateStack(self, data):
        stack = data.callersStack()
        index = -1
        for index, caller in enumerate(stack):
            if caller[3].endswith("<module>") or ():
                break
        if index!=-1:
            stack = stack[:index]
            breadcrumbs = self._createBreadcrumbs(stack)
        else:
            breadcrumbs = data.filename()
        self.lineEdit_TestScriptName.setText(breadcrumbs)
    def _createBreadcrumbs(self, stack):
        s = []
        for caller in stack:
            filename, _ext = os.path.splitext(os.path.basename(caller[1]))
            lineNumber = caller[2]
            s.append("%(F)s#%(N)s"%{"F":filename, "N":lineNumber})
        s.reverse()
        return "...".join(s)
    def _addMarker(self, colour, lineNumber=None):
        self.textEdit.setMarkerBackgroundColor(colour, self.ARROW_MARKER_NUM)
        if lineNumber!=None:
            lineNumber = self._lineNumber
        self.textEdit.markerDeleteAll()
        self.textEdit.markerAdd(lineNumber-1, self.ARROW_MARKER_NUM)
    def _prepMarker(self, lineNumber):
        self.textEdit.ensureCursorVisible()
        self.textEdit.setCaretLineVisible(True)
        self.textEdit.ensureLineVisible(lineNumber)
        self.textEdit.setCursorPosition(lineNumber, 0)
    def _onRunnerFinished(self):
        self.textEdit.markerDeleteAll()
        text = str(self.lineEdit_TestScriptName.text())+" = FINISHED"
        self.lineEdit_TestScriptName.setText(text)

def configureQScintilla(widget, parent):
    widget.setCaretLineVisible(True)
    lexer = QsciLexerPython()
    font = QtGui.QFont()
    font.setFamily("Consolas")
    font.setFixedPitch(True)
    font.setPointSize(10)
    fm = QtGui.QFontMetrics(font)
    widget.setFont(font)
    widget.setIndentationGuides(True)
    widget.setIndentationsUseTabs(False)
    widget.setIndentationWidth(4)
    widget.setWrapMode(False)
    widget.setWhitespaceVisibility(True)
    widget.setEolVisibility(True)
    widget.setAutoIndent(True)
    widget.setMarginsFont(font)
    widget.setLexer(lexer)
    widget.setCaretLineVisible(True)
    widget.setCaretLineBackgroundColor(QtGui.QColor("#CDA869"))
    widget.setFolding(QsciScintilla.BoxedTreeFoldStyle)
    widget.setEdgeMode(QsciScintilla.EdgeLine)
    widget.setEdgeColumn(120)
    widget.setEdgeColor(QtGui.QColor("#FF0000"))
    widget.setBraceMatching(QsciScintilla.SloppyBraceMatch)
    widget.setMarginWidth(0, fm.width("00000") + 0)
    widget.setMarginsBackgroundColor(QtGui.QColor("#333333"))
    widget.setMarginsForegroundColor(QtGui.QColor("#CCCCCC"))
    widget.setFoldMarginColors(QtGui.QColor("#99CC66"),QtGui.QColor("#333300"))
    size = parent.size()
    widget.resize(size)
    return widget

class Scripts(QtGui.QFrame):
    RESOURCE_NAME = "Scripts.ui"
    ICON_STEP  = "icon_step.png"
    ICON_STOP  = "icon_stop.png"
    ICON_START = "icon_start.png"
    TEXT_NO_RESULT = "No result"
    TEXT_NOT_EXECUTED = "Not executed"
    TEXT_ABORED = "Aborted"
    def __init__(self, parent):
        super(Scripts, self).__init__(parent=parent)
        self._parent = parent
        self._settings = parent._settings
        self._getWindowId = lambda: self._windowId
        self._windowId = None       #    Set this whenever the video window container is changed.
        self._resourcePath = self._parent._resourcePath
        self.__waitOnEvent = False
        self._context = Context()
    def show(self):
        super(Scripts, self).show()
        self._windowId = self.Widget_videoContainer.winId()
        self.connect(self, Qt.SIGNAL('apiLoad(PyQt_PyObject, int)'), self._onApiLoad, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL('apiRequires(PyQt_PyObject, int)'), self._onApiRequires, QtCore.Qt.QueuedConnection)
        self.connect(self.button_Start, SIGNAL('clicked()'), self._onStartStop, QtCore.Qt.QueuedConnection)
        self.connect(self.button_Step, SIGNAL('clicked()'), self._onStep, QtCore.Qt.QueuedConnection)
        self.connect(self.checkBox_enabledStepping, Qt.SIGNAL("stateChanged(int)"), self._onEnableStepping, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL("runnerTestStarted(PyQt_PyObject)"), self._onRunnerTestStarted, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL("runnerTestFinished(PyQt_PyObject)"), self._onRunnerTestFinished, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL("runnerFailure(PyQt_PyObject, int)"), self._onRunnerFailure, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL("runnerError(PyQt_PyObject, int)"), self._onRunnerError, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL("runnerFinished(int)"), self._onRunnerFinished, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL("runnerResults(PyQt_PyObject, int)"), self._onRunnerResults, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL("runnerEvent(PyQt_PyObject, int)"), self._onRunnerEvent, QtCore.Qt.QueuedConnection)
        self.connect(self, Qt.SIGNAL("breakpointReached(PyQt_PyObject, int)"), self._onBreakpointReached, QtCore.Qt.QueuedConnection)
        self.connect(self._parent.action_EventsDumpFile, SIGNAL('triggered()'), self._onDumpEventsToFile, QtCore.Qt.QueuedConnection)
        self.connect(self._parent.action_EventsDumpConsole, SIGNAL('triggered()'), self._onDumpEventsToConsole, QtCore.Qt.QueuedConnection)
        self.tableWidget_scripts.clearContents()
        self.tableWidget_scripts.setRowCount(0)
        self._addTests(self._parent._args.script)
        self._iconStep  = QtGui.QIcon(QtGui.QPixmap(os.path.join(self._resourcePath, "icons", Scripts.ICON_STEP)))
        self._iconStop  = QtGui.QIcon(QtGui.QPixmap(os.path.join(self._resourcePath, "icons", Scripts.ICON_STOP)))
        self._iconStart = QtGui.QIcon(QtGui.QPixmap(os.path.join(self._resourcePath, "icons", Scripts.ICON_START)))
        self.button_Step.setIcon(self._iconStep)
        self.button_Start.setIcon(self._iconStart)
        self.loadUi()
    def close(self):
        self._stopScript()
        return True
    def saveUi(self, settings=None):
        if settings==None:
            settings = self._settings
        settings.beginGroup("scripts")
        settings.remove("")
        try:
            pass
        finally:
            settings.endGroup()
            settings.sync()
    def loadUi(self, settings=None):
        if settings==None:
            settings = self._settings
        settings.beginGroup("scripts")
        try:
            pass
        finally:
            settings.endGroup()
    def _onDumpEventsToConsole(self):
        self._parent._events.dump()
    def _onDumpEventsToFile(self):
        filename = QtGui.QFileDialog.getSaveFileName(self, "Save event dump to file")
        if filename:
            writer = open(str(filename), "w")
            try:
                self._parent._events.dump(writer)
            finally:
                writer.close()
    def _onEnableStepping(self, state):
        if state==QtCore.Qt.Unchecked:
            self._parent._events("APP-STEPPING DISABLE")
            self.__waitOnEvent = False
            #    Set the run going if already paused:
            sctx = self._context()
            if sctx:
                sctx.put(TRCommands.STEP)
        else:
            self._parent._events("APP-STEPPING ENABLE")
            self.__waitOnEvent = True
            sctx = self._context()
            if sctx:
                sctx.put(TRCommands.STALL)
    def _onRunnerFailure(self, exc, uId):
        self._parent._events("RUNNER-FAILURE", exc)
    def _onRunnerError(self, exc, uId):
        self._parent._events("RUNNER-ERROR", exc)
        self.button_Start.setText('Start')
        self.button_Start.setIcon(self._iconStart)
        self._cleanupRunner(uId)
    def _onRunnerFinished(self, uId):
        self._parent._events("RUNNER-FINISHED")
        self._parent.emit(Qt.SIGNAL("runnerFinished(int)"), uId)
        self._cleanupRunner(uId)
    def _onRunnerResults(self, results, uId):
        self._parent._events("RUNNER-RESULTS", results)
        for scriptName, result in results.items():
            self._retireResult(scriptName, result.result())
    def _retireResult(self, scriptName, result):
        isErr = isinstance(result, Exception)
        if isErr:
            r = "Exception: %(E)s"%{"E":str(result)}
        else:
            r = "all ok"
        self._updateTestResult(scriptName, r, isErr)
    def _onRunnerTestStarted(self, scriptName):
        self._parent._events("SCRIPT-START", scriptName)
        self._updateTest(scriptName, "Script Started")
    def _onRunnerTestFinished(self, (scriptName, result)):
        self._parent._events("SCRIPT-FINISHED", scriptName)
        self._updateTest(scriptName, "Script Finished")
        self._parent._events("RUNNER-RESULT", result)
        self._retireResult(scriptName, result.result())
    def _updateTest(self, scriptName, state):
        tableName = self.tableWidget_scripts
        scriptKey = scriptName.getRelPath()
        scriptMethodKey = scriptName.methodName()
        for row in xrange(tableName.rowCount()):
            item = tableName.item(row, 0)
            item1 = tableName.item(row, 1)
            if (str(item.text())==scriptKey) and (str(item1.text())==scriptMethodKey):
                item = tableName.item(row, 2)
                item.setText(state)
                break
        tableName.resizeColumnsToContents()
    def _updateTestResult(self, scriptName, result, isErr=False):
        tableName = self.tableWidget_scripts
        if isErr:
            #    Colour the item red.
            colour = Qt.QColor(255, 0, 0)
        else:
            #    Colour the item green.
            colour = Qt.QColor(0, 255, 0)
        found = False
        scriptKey = scriptName.getRelPath()
        scriptMethodKey = scriptName.methodName(defaultValue="")
        for row in xrange(tableName.rowCount()):
            item = tableName.item(row, 0)
            item1 = tableName.item(row, 1)
            if (str(item.text())==scriptKey) and (str(item1.text())==scriptMethodKey):
                item = tableName.item(row, 3)
                item.setBackgroundColor(colour)
                item.setText(result)
                tableName.resizeColumnsToContents()
                found=True
                break
        if found==False:
            #    Add it!
            self._addTests([scriptName])
    def _addTests(self, scripts):
        #    type(scripts)=[TVector]
        tableName = self.tableWidget_scripts
        for script in scripts:
            moduleName = script.getRelPath()
            methodName = script.methodName(defaultValue="")
            tableName.insertRow(0)
            item = QtGui.QTableWidgetItem(moduleName)
            tableName.setItem(0, 0, item)
            item = QtGui.QTableWidgetItem(methodName)
            tableName.setItem(0, 1, item)
            item = QtGui.QTableWidgetItem(Scripts.TEXT_NOT_EXECUTED)
            tableName.setItem(0, 2, item)
            item = QtGui.QTableWidgetItem(Scripts.TEXT_NO_RESULT)
            tableName.setItem(0, 3, item)
        tableName.resizeColumnsToContents()
    def _clearTests(self):
        tableName = self.tableWidget_scripts
        colour = Qt.QColor(255, 255, 255)
        for row in xrange(tableName.rowCount()):
            item = tableName.item(row, 2)
            item.setText("Not executed")
            item = tableName.item(row, 3)
            item.setText("No result")
            item.setBackgroundColor(colour)
        tableName.resizeColumnsToContents()
    def _cleanupRunner(self, uId=None):
        self.button_Start.setText('Start')
        self.button_Start.setIcon(self._iconStart)
        self.button_Step.setEnabled(False)
        self._stopRunnerStepListener(uId)
        self._context.destroy(uId)
    def _onStartStop(self):
        #    Control the playback execution.
        sctx = self._context()
        if sctx==None:
            self._clearTests()
            self._parent._events("RUNNER-START")
            sctx = self._context.new()
            with sctx:
                self.tableWidget_apiData.clearContents()
                self.tableWidget_apiData.setRowCount(0)
                self.button_Start.setText("Stop")
                self.button_Start.setIcon(self._iconStop)
                uId = sctx._uId
                global testingDebugLevel
                debugger = Debugger(testingDebugLevel)
                runner = threading.Thread(target=runTestRunner, args=[copy.deepcopy(self._parent._args), sctx, self._getWindowId, self, debugger])
                sctx._runner = runner
                runner.setDaemon(True)
                runner.setName("TestRunner_%(I)s"%{"I":uId})
                self._parent._events("RUNNER-CREATE")
                runner.start()
                self._parent._events("RUNNER-START")
                sctx.put(TRCommands.RUN)
        else:
            self._stopScript()
    def _stopScript(self):
        sctx = self._context()
        if sctx!=None:
            self.button_Start.setIcon(self._iconStart)
            self._parent._events("APP-STOP")
            self._parent._events("RUNNER-STOP")
            sctx.put(TRCommands.TEARDOWN)
            #    Set the current scripts as aborted.
            self._setAbortAll()
    def _setAbortAll(self):
        tableName = self.tableWidget_scripts
        for row in xrange(tableName.rowCount()):
            item = tableName.item(row, 2)
            if str(item.text())==Scripts.TEXT_NO_RESULT:
                item.setText(Scripts.TEXT_ABORED)
    def _onStep(self):
        r"""
        @summary: Single-step over the next api call:
        """
        self._parent._events("APP-STEP")
        sctx = self._context()
        if sctx!=None:
            with sctx:
                if sctx._runner!=None and sctx._testRunner!=None:
                    self._parent.emit(Qt.SIGNAL("apiExecuting()"))
                    self.button_Step.setEnabled(False)
                    self._parent._events("RUNNER-STEP")
                    sctx.put(TRCommands.STEP)
    def _onApiLoad(self, data, uId):
        self._renderApiData(data)
    def _onApiRequires(self, data, uId):
        return self._renderApiData(data)
    def _getWaitOnEvent(self):
        return self.__waitOnEvent
    def _onRunnerEvent(self, event, uId):
        sctx = self._context()      #    Get the current SubContext:
        if sctx and sctx._uId==uId:
            with sctx:
                #    (re) Start a thread to listen for stepped events.
                self._stopRunnerStepListener(uId)
                def listen():
                    (eventNotifierEntry, eventNotifierContinue) = event
                    while sctx._runnerEnabled==True:
                        if eventNotifierEntry.wait(timeout=0.1)==True:
                            data = eventNotifierEntry.data()
                            #    This guarantees eventNotifierEntry.data() integrity:
                            eventNotifierEntry.reset()
                            eventNotifierEntry.clear()
                            eventNotifierContinue.set()
                            self.emit(Qt.SIGNAL("breakpointReached(PyQt_PyObject, int)"), data, uId)
                t = threading.Thread(target=listen)
                t.setName("RunnerStepListener_%(I)s"%{"I":uId})
                t.setDaemon(True)
                sctx._runnerEnabled = True
                t.start()
                sctx._runnerStepListener = t
    def _stopRunnerStepListener(self, uId=None):
        sctx = self._context(uId)
        if sctx and sctx._runnerStepListener!=None:
            #    This should kill the thread:
            sctx._runnerEnabled = False
            sctx._runnerStepListener.join()
            sctx._runnerStepListener = None
    def _onBreakpointReached(self, data, uId):
        sctx = self._context()
        if sctx and sctx._uId==uId:
            steppingEnabled = self.checkBox_enabledStepping.isChecked()
            if steppingEnabled:
                self.button_Step.setEnabled(True)
                self._parent._events("RUNNER-BREAKPOINT")
            else:
                #    Automatically let the test continue:
                sctx.put(TRCommands.STEP)
                self._parent.emit(Qt.SIGNAL("apiExecuting()"))
            #    Now update the api data:
            if data!=None:
                isErr = self._insertApiData(data)
                if steppingEnabled:
                    if isErr==False:
                        self.button_Step.setEnabled(True)
                    else:
                        self.button_Step.setEnabled(False)
                self._parent.emit(Qt.SIGNAL("followCode(PyQt_PyObject)"), data)
    def _insertApiData(self, data):
        return self._renderApiData(data)
    def _formatApiDataNotificationEvent(self, data):
        if isinstance(data, BaseApiNotification):
            args = []
            kwargs = {"info":str(data)}
        else:
            if isinstance(data, CallBreakpoint):
                args = [data.name()]
                args = [data.apid().ns()+"."+args[0]]
                args.extend(data.args())
                kwargs = data.kwargs()
            elif isinstance(data, ManipulationBreakpoint):
                args = data.whats()
                kwargs = {"mode":data.mode()}
        args = tuple(args)
        self._parent._events("API-CALL-COMPLETE", data.filename(), *args, **kwargs)
    def _renderApiData(self, data):
        self._formatApiDataNotificationEvent(data)
        tableName = self.tableWidget_apiData
        row = 0     #    Always insert at the top:
        if isinstance(data, (PreApiCallBreakpoint, BaseApiNotification)):
            #    Complete the row when we reach the breakpoint.
            tableName.insertRow(row)
        def formatRow(data):
            cols = []
            NA = "N/A"
            args = NA
            kwargs = NA
            name = NA
            duration = NA
            result = NA
            ns = NA
            path = NA
            moduleName = NA
            clazzName = NA
            version = NA
            if isinstance(data, BaseNotification):
                timeStart = data.timeStart()
                try:
                    result = data.result()
                except:
                    pass
                filename = data.filename()
                lineNumber = data.lineNumber()
                if isinstance(data, BaseApiNotification):
                    args = data.what()
                    if isinstance(data, ApiRequires):
                        args_ = []
                        for w in args:
                            args_.append(str(w))
                        args = " | ".join(args_)
                    kwargs = ""
                    name = data.name()
                else:
                    if isinstance(data, CallBreakpoint):
                        args = data.args()
                        kwargs = data.kwargs()
                        name = data.name()
                        apid = data.apid()
                        #    Decode:
                        ns = apid.ns()
                        path = apid.path()
                        moduleName = apid.moduleName()
                        clazzName = apid.clazzName()
                        version = apid.api().VERSION
                    elif isinstance(data, ManipulationBreakpoint):
                        args = str(data.mode())
                        kwargs = {"apis": data.whats()}
                        name = "__loads__"
                try:
                    duration = data.timeEnd()-timeStart
                except:
                    pass
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":timestamp(timeStart)}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":duration}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":name}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":args}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":kwargs}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":result}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":filename}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":lineNumber}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":ns}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":path}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":moduleName}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":clazzName}))
                cols.append(QtGui.QTableWidgetItem("%(T)s"%{"T":version}))
                if duration==name==args==kwargs==NA:
                    pass
                try:
                    isErr = data.isErr()
                except:
                    isErr = False
                return (isErr, cols)
        (isErr, cols) = formatRow(data)
        for col, item in enumerate(cols):
            tableName.setItem(row, col, item)
        tableName.resizeColumnsToContents()
        return isErr

class BaseEditor(QtGui.QFrame):
    ICON_FILEOPEN = "icon_file_open.png"
    ICON_FILESAVE = "icon_file_save.png"
    ICON_FILESAVEAS = "icon_file_saveas.png"
    ICON_FILEREADONLY = "icon_file_readonly.png"
    ICON_FILEWRITABLE = "icon_file_writable.png"
    def __init__(self, parent):
        super(BaseEditor, self).__init__(parent=parent)
        self._parent = parent
        self._settings = parent._settings
        self._readOnly = True
        self._filename = ""
        self._apiMethodNames = []
        self._ignoreEdit = False
        self._dirty = False
    def loadUi(self, settings=None):
        if settings==None:
            settings = self._settings
        settings.beginGroup(self._key)
        try:
            self._loadUi(settings)
        finally:
            settings.endGroup()
        self._dirty = False
        self._render()
    def _loadUi(self, settings):
        filename = settings.value("filename").toString()
        if len(filename)>0:
            self._filename = filename
        self._readOnly = settings.value("readOnly").toBool()
    def saveUi(self, settings=None):
        if settings==None:
            settings = self._settings
        settings.beginGroup(self._key)
        settings.remove("")
        try:
            self._saveUi(settings)
        finally:
            settings.endGroup()
    def _saveUi(self, settings):
        settings.setValue("filename", self._filename)
        settings.setValue("readOnly", self._readOnly)
    def close(self):
        if self._dirty==True:
            if self._readOnly==False:
                onSave = self._onSave
            else:
                onSave = self._onSaveAs
            result = QtGui.QMessageBox.question(self,
                                       "Application closing",
                                       self._savePrompt,
                                       buttons=QtGui.QMessageBox.Yes | QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel
                                       )
            if result==QtGui.QMessageBox.Yes:
                onSave()
            elif result==QtGui.QMessageBox.Cancel:
                return False
        return True
    def _onSave(self):
        if (self._filename!=None) and (len(self._filename)>0):
            open(self._filename, "w").write(str(self.textEdit.text()))
            self._dirty = False
            self._renderButtons()
    def _onSaveAs(self):
        if (self._filename!=None) and (len(self._filename)>0):
            location = os.path.realpath(os.path.dirname(self._filename))
        else:
            location = os.path.realpath(self._parent._args.script_root)
        filename = QtGui.QFileDialog.getSaveFileName(self, "Save as...", location)
        if (filename!=None) and (len(filename)>0):
            open(filename, "w").write(str(self.textEdit.toPlainText()))
            self._filename = filename
            self._dirty = False
            self._renderButtons()
    def _onOpen(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Open file...", self._filename)
        if len(filename)>0:
            self._loadFile(filename)
    def _loadFile(self, filename):
        self._ignoreEdit = True
        self.textEdit.clear()
        self._ignoreEdit = False
        try:
            self.textEdit.setText(open(filename, "r").read())
            self.emit(Qt.SIGNAL("fileLoaded(PyQt_PyObject)"), filename)
        except Exception, _e:
            pass
        self._filename = os.path.realpath(str(filename))
        self._dirty = False
    def _onTextChanged(self):
        if self._ignoreEdit==False:
            self._dirty = True
            self._renderButtons()
    def _render(self):
        self._ignoreEdit = True
        self.textEdit.clear()
        self._ignoreEdit = False
        filename = self._filename
        if filename!=None and len(filename)>0:
            self._loadFile(self._filename)
        self._renderButtons()
    def _renderButtons(self):
        isReadOnly = self._readOnly
        self.textEdit.setReadOnly(isReadOnly)
        if isReadOnly==True:
            self.pushButton_ToggleReadOnly.setText("write")
            self.pushButton_ToggleReadOnly.setIcon(self._iconReadonly)
            for button in self._saveButtons:
                button.setEnabled(False)
        else:
            self.pushButton_ToggleReadOnly.setText("Read only")
            self.pushButton_ToggleReadOnly.setIcon(self._iconWritable)
            isDirty = self._dirty
            for button in self._saveButtons:
                button.setEnabled(isDirty)
    def _onToggleReadOnly(self):
        readOnly = "Read only"
        self._readOnly = str(self.pushButton_ToggleReadOnly.text())==readOnly
        if self._readOnly==True:
            self.pushButton_ToggleReadOnly.setText("write")
        else:
            self.pushButton_ToggleReadOnly.setText(readOnly)
        self._renderButtons()
    def show(self):
        super(BaseEditor, self).show()
        self.textEdit = QsciScintilla(self.frame_editor)
        configureQScintilla(self.textEdit, self.frame_editor)
        self._saveButtons = [self.pushButton_SaveAs, self.pushButton_Save]
        self.connect(self.pushButton_Open, SIGNAL('clicked()'), self._onOpen)
        self.connect(self.pushButton_Save, SIGNAL('clicked()'), self._onSave)
        self.connect(self.pushButton_SaveAs, SIGNAL('clicked()'), self._onSaveAs)
        self.connect(self.pushButton_ToggleReadOnly, SIGNAL('clicked()'), self._onToggleReadOnly)
        self.connect(self.textEdit, Qt.SIGNAL("textChanged()"), self._onTextChanged)
        self.connect(self, Qt.SIGNAL("fileLoaded(PyQt_PyObject)"), self._onFileLoaded, QtCore.Qt.QueuedConnection)
        size = self.frame_editor.size()
        self._iconOpen  = QtGui.QIcon(QtGui.QPixmap(os.path.join(self._parent._resourcePath, "icons", BaseEditor.ICON_FILEOPEN)))
        self._iconSave  = QtGui.QIcon(QtGui.QPixmap(os.path.join(self._parent._resourcePath, "icons", BaseEditor.ICON_FILESAVE)))
        self._iconSaveAs  = QtGui.QIcon(QtGui.QPixmap(os.path.join(self._parent._resourcePath, "icons", BaseEditor.ICON_FILESAVEAS)))
        self._iconReadonly  = QtGui.QIcon(QtGui.QPixmap(os.path.join(self._parent._resourcePath, "icons", BaseEditor.ICON_FILEREADONLY)))
        self._iconWritable  = QtGui.QIcon(QtGui.QPixmap(os.path.join(self._parent._resourcePath, "icons", BaseEditor.ICON_FILEWRITABLE)))
        self.pushButton_Open.setIcon(self._iconOpen)
        self.pushButton_Save.setIcon(self._iconSave)
        self.pushButton_SaveAs.setIcon(self._iconSaveAs)
        self.textEdit.resize(size)
    def _onFileLoaded(self):
        pass
    def getFilename(self):
        return self._filename
    @staticmethod
    def _crudeGetApi(filename):
        methodNames = []
        lines = open(filename, "r").read().splitlines()
        for line in lines:
            line = line.strip()
            pre, match, post = line.partition("def ")
            if match and post:
                pre, match, post = post.partition("(")
                if match and post:
                    if not pre.startswith("_"):
                        methodNames.append(pre)
        return methodNames
    def resizeEvent(self, event):
        newSize = event.size()
        targetSize = QtCore.QSize(newSize.width()-25, newSize.height()-80)
        self.textEdit.resize(targetSize)

def runRunner(sctx, lock, mainLoop, q):
    runner = sctx._testRunner
    uId = sctx._uId
    debugger = runner.debugger()
    runner.setup(mainLoop, q)
    lock.release()
    debugger.debug("running...1")
    try:
        runner.run(uId)
    except UITestFailure as e:
        debugger.error(traceback.format_exc())
        debugger.error("FAIL: %(E)s."%{"E":str(2)})
        screenshot = e.screenshot()
        if screenshot:
            name = os.path.join(runner.getResultsDir(), "screenshot.png")
            saveFrame(e.screenshot(), name)
            debugger.debug("Saved screenshot to '%(S)s'."%{"S":name})
        sctx.put(TRCommands.RESULT, data=runner.getResults())
        sctx.put(e)
    except Exception, _e:
        debugger.debug("Ran with error...\n%(T)s"%{"T":traceback.format_exc()})
        sctx.put(TRCommands.RESULT, data=runner.getResults())
        sctx.put(TRCommands.RAN)
    else:
        debugger.debug("Ran...")
        sctx.put(TRCommands.RESULT, data=runner.getResults())
        sctx.put(TRCommands.RAN)
    finally:
        debugger.debug("running...3")
        runner.teardown()
        debugger.debug("running...4")

def runTestRunner(args, sctxt, getWindowId, parent, debugger):
    uId = sctxt._uId
    q = sctxt._q
    debugger.debug("run[%(U)s]"%{"U":uId})
    try:
        while True:
            try:
                data = q.get(block=True, timeout=1)
            except Empty:
                pass
            except (IOError, EOFError), _e:
                debugger.warn("IOError[%(U)s]: probably due to teardown()!"%{"U":uId})
                break
            else:
                cmd = data.cmd
                if data.uId!=uId:
                    debugger.warn("Stale command[%(U)s]: ignoring, given: %(G)s."%{"G":data.uId, "U":uId})
                    continue
                if isinstance(cmd, Exception):
                    parent.emit(Qt.SIGNAL("runnerFailure(PyQt_PyObject, int)"), data, uId)
                    break
                if cmd==TRCommands.TEARDOWN:
                    with sctxt:
                        if sctxt._testRunner!=None:
                            sctxt._testRunner.teardown()
                    break
                elif cmd==TRCommands.RUN:
                    debugger.debug("playback begin.")
                    def onEventNotifier(event):
                        #    We need to know when the api is ready to step, so listen to the Event object:
                        parent.emit(Qt.SIGNAL("runnerEvent(PyQt_PyObject, int)"), event, uId)
                    sctxt._testRunner = TestPlayback(args, getWindowId=getWindowId, waitOnEvent=parent._getWaitOnEvent, notifier=onEventNotifier)
                    sctxt._testRunner.ignoreEvents(False)
                    lock = Semaphore(0)
                    t = threading.Thread(target=runRunner, args=[sctxt, lock, parent._parent._mainLoop, q])
                    t.setName("Runner_%(I)s"%{"I":uId})
                    t.setDaemon(True)
                    t.start()
                    lock.acquire()
                elif cmd==TRCommands.RUNNING_START:
                    debugger.debug("Test started: %(N)s"%{"N":data.data})
                    parent.emit(Qt.SIGNAL("runnerTestStarted(PyQt_PyObject)"), data.data)
                elif cmd==TRCommands.RUNNING_FINISHED:
                    (scriptName, _result) = data.data
                    debugger.debug("Test finished: %(N)s"%{"N":scriptName})
                    parent.emit(Qt.SIGNAL("runnerTestFinished(PyQt_PyObject)"), data.data)
                elif cmd==TRCommands.RAN:
                    debugger.debug("playback finished.")
                    break
                elif cmd==TRCommands.RESULT:
                    debugger.debug("test script results in!")
                    parent.emit(Qt.SIGNAL("runnerResults(PyQt_PyObject, int)"), data.data, uId)
                elif cmd==TRCommands.STEP:
                    with sctxt:
                        if sctxt._testRunner!=None:
                            sctxt._testRunner.step()
                elif cmd==TRCommands.STALL:
                    with sctxt:
                        if sctxt._testRunner!=None:
                            sctxt._testRunner.stall()
                elif cmd==TRCommands.API_LOAD:
                    d = data.data
                    debugger.debug("API-LOAD: '%(W)s' from '%(S)s' result '%(R)s'"%{"S":d.scriptName(), "W":d.what(), "R":d.result()})
                    parent.emit(Qt.SIGNAL("apiLoad(PyQt_PyObject, int)"), d, uId)
                elif cmd==TRCommands.API_REQUIRES:
                    d = data.data
                    debugger.debug("API-REQUIRES: '%(W)s' from '%(S)s' result '%(R)s'"%{"S":d.scriptName(), "W":d.what(), "R":d.result()})
                    parent.emit(Qt.SIGNAL("apiRequires(PyQt_PyObject, int)"), d, uId)
    except Exception, e:
        traceback.print_exc()
        parent.emit(Qt.SIGNAL("runnerError(PyQt_PyObject, int)"), e, uId)
    finally:
        print "run finished!"
        parent.emit(Qt.SIGNAL("runnerFinished(int)"), uId)

if __name__ == '__main__':
    mainLoop = glib.MainLoop()      #@UndefinedVariable
    gobject.threads_init()          #@UndefinedVariable
    qApp = QApplication(sys.argv)
    qApp.connect(qApp, SIGNAL('lastWindowClosed()'), qApp, SLOT('quit()'))
    args = parseArgs()
    def wrapArgs(args):
        for index, script in enumerate(args.script):
            args.script[index] = TVector(filename=os.path.realpath(script), root=os.path.realpath(args.script_root))
    if len(args.script_root)>0:
        #    Now the tests can import each-other:
        path = os.path.realpath(args.script_root)
        sys.path.append(path)
    args.project_root = os.path.realpath(os.path.join(os.path.dirname(__file__), "../"))
    wrapArgs(args)
    #    Now dynamically create the apis in the factory:
    ApiFactory.create(args.api_types)
    if args.nose==True:
        discover(args)
    resourcePath = path = os.path.join("StbTester", "playback", "ui")
    path = os.path.join(resourcePath, "QtTestRunnerNew.ui")
    qtStbtRun = QtStbtRun(args, mainLoop, resourcePath)
    uic.loadUi(path, qtStbtRun)
    qtStbtRun.show()
    sys.exit(qApp.exec_())
