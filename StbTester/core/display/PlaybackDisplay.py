'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.core.display.BaseDisplay import BaseDisplay
from StbTester.core.utils.GObjectTimeout import GObjectTimeout
from StbTester.core.utils.MessageIterator import MessageIterator
from StbTester.core.utils.PathUtils import mkdir
import gst
import sys
import time

class PlaybackDisplay(BaseDisplay):
    def __init__(self, sourcePipelineDescription, sinkPipelineDescription, debugger, mainLoop, getWindowId=None):
        super(PlaybackDisplay, self).__init__(debugger, getWindowId)
        self._mainloop = mainLoop
#        glib.MainLoop()
#        gobject.threads_init()
        imageprocessing = " ! ".join([
                # Buffer the video stream, dropping frames if downstream
                # processors aren't fast enough:
                "queue name=q leaky=2",
                # Convert to a colorspace that templatematch can handle:
                "ffmpegcolorspace",
                # Detect motion when requested:
                "stbt-motiondetect name=motiondetect enabled=false",
                # OpenCV image-processing library:
                "stbt-templatematch name=template_match method=1", # TODO: Why is this enabled by default? Can it be disabled?
                ])
        xvideo = " ! ".join([
                            # Convert to a colorspace that xvimagesink can handle:
                            "ffmpegcolorspace",
                            sinkPipelineDescription,
                            ])
        screenshot = ("appsink name=screenshot max-buffers=1 drop=true sync=false")
        pipe = " ".join([
                        imageprocessing,
                        "! tee name=t",
                        "t. ! queue leaky=2 !", screenshot,
                        "t. ! queue leaky=2 !", xvideo
                        ])
        """
        Gstreamer loads plugin libraries on demand, when elements that need
        those libraries are first mentioned. There is a bug in gst-opencv
        where it erroneously claims to provide appsink, preventing the
        loading of the real appsink -- so we load it first.
        TODO: Fix gst-opencv so that it doesn't prevent appsink from being loaded.
        """
        gst.parse_launch("appsink")
        self._sourcePipelineDescription = sourcePipelineDescription
        self._sourceBin = self._createSourceBin()
        self._sinkBin = gst.parse_bin_from_description(pipe, True)
        self._setPipeline(gst.Pipeline("stb-tester"))
        self._pipeline.add(self._sourceBin, self._sinkBin)
        gst.element_link_many(self._sourceBin, self._sinkBin)
        self._templateMatch = self._pipeline.get_by_name("template_match")
        self._motionDetect = self._pipeline.get_by_name("motiondetect")
        self._setScreenshot(self._pipeline.get_by_name("screenshot"))
        self._bus = self._pipeline.get_bus()
        self._bus.add_signal_watch()
        self._bus.enable_sync_message_emission()
        self._bus.connect("message::error", self._onError)
        self._bus.connect("message::warning", self._onWarning)
        self._bus.connect("sync-message::element", self._onSyncMessage)
        if self._debugger.level()>1:
            if mkdir("stbt-debug/motiondetect") and mkdir(
                      "stbt-debug/templatematch"):
                # Note that this will dump a *lot* of files -- several images
                # per frame processed.
                self._motionDetect.props.debugDirectory = ("stbt-debug/motiondetect")
                self._templateMatch.props.debugDirectory = ("stbt-debug/templatematch")
            else:
                self._debugger.warn("Failed to create directory 'stbt-debug'. "
                     "Will not enable motiondetect/templatematch debug dump.")
        self._pipeline.set_state(gst.STATE_PLAYING)
        # Handle loss of video (but without end-of-stream event) from the
        # Hauppauge HDPVR capture device.
        self._queue = self._pipeline.get_by_name("q")
        self._testTimeout = None
        self._successiveUnderruns = 0
        self._underrunTimeout = None
        self._queue.connect("underrun", self._onUnderrun)
        self._queue.connect("running", self._onRunning)
    def _createSourceBin(self):
        sourceBin = gst.parse_bin_from_description(self._sourcePipelineDescription+" ! capsfilter name=padforcer caps=video/x-raw-yuv", False)
        self._pad = gst.GhostPad("source", sourceBin.get_by_name("padforcer").src_pads().next())
        sourceBin.add_pad(self._pad)
        return sourceBin
    def captureScreenshot(self):
        return self._screenshot.get_property("last-buffer")
    def detect(self, elementName, params, timeoutSecs, checkAborted=lambda: False):
        """
        Generator that yields the messages emitted by the named gstreamer
        element configured with the parameters `params`.

        "elementName" is the name of the gstreamer element as specified in the
        pipeline. The name must be the same in the pipeline and in the messages
        returned by gstreamer.

        "params" is a dictionary of parameters to setup the element. The
        original parameters will be restored at the end of the call.

        "timeoutSecs" is in seconds elapsed, from the method call. Note that
        stopping iterating also enables to interrupt the method.

        For every frame processed, a tuple is returned: (message, screenshot).
        """
        self._debugger.debug(">> detect <<")
        element = self._pipeline.get_by_name(elementName)
        paramsBackup = {}
        for key in params.keys():
            paramsBackup[key] = getattr(element.props, key)
        try:
            for key in params.keys():
                setattr(element.props, key, params[key])
            """
            Timeout after 5s in case no messages are received on the bus.
            This happens when starting a new instance of stbt when the
            Hauppauge HDPVR capture device is stopping.
            """
            with GObjectTimeout(timeoutSecs=5, handler=self._onTimeout) as t:
                checkAborted()
                self._testTimeout = t
                self._startTimestamp = None
                for message in MessageIterator(self._bus, "message::element", self._mainloop, checkAborted):
                    # Cancel test_timeout as messages are obviously received.
                    if self._testTimeout:
                        self._testTimeout.cancel()
                        self._testTimeout = None
                    st = message.structure
                    if st.get_name()==elementName:
                        buf = self._screenshot.get_property("last-buffer")
                        if not buf:
                            continue
                        if not self._startTimestamp:
                            self._startTimestamp = buf.timestamp
                        try:
                            if ((buf.timestamp-self._startTimestamp) > (timeoutSecs*100000000000)):
                                return
                        except Exception, _e:
                            pass
                        yield (st, buf)
        finally:
            for key in params.keys():
                setattr(element.props, key, paramsBackup[key])
    def _onTimeout(self):
        self._debugger.warn("Timed out")
        self._mainloop.quit()
        # stop the timeout from running again
        return False
    def _onError(self, bus, message):
        assert message.type == gst.MESSAGE_ERROR
        err, dbg = message.parse_error()
#        raise RuntimeError("%s: %s\n%s\n"%(err, err.message, dbg))
        self._debugger.error("Error: %s: %s\n%s" % (err, err.message, dbg))
        sys.exit(1)
    def _onWarning(self, bus, message):
        assert message.type == gst.MESSAGE_WARNING
        err, dbg = message.parse_warning()
        self._debugger.warn("Warning: %s: %s\n%s\n"%(err, err.message, dbg))
        if (err.message == "OpenCV failed to load template image" or err.message == "OpenCV failed to load mask image"):
#            raise RuntimeError("%s: %s\n%s\n"%(err, err.message, dbg))
            self._debugger.error("Error: %s" % err.message)
            sys.exit(1)
    def _onSyncMessage(self, bus, message):
        self._debugger.ddebug("on_sync_message/")
        if message.structure is None:
            return
        message_name = message.structure.get_name()
        if message_name == "prepare-xwindow-id":
            imagesink = message.src
            win_id = self.getWindowId()
            if win_id!=None:
                #    This disables stretch of video:
                imagesink.set_property("force-aspect-ratio", True)
                imagesink.set_xwindow_id(win_id)
        self._debugger.ddebug("/on_sync_message")
    def _onUnderrun(self, element):
        """
        Cancel test_timeout as messages are obviously received on the bus.
        """
        self._debugger.ddebug("onUnderrun/")
        if self._testTimeout:
            self._testTimeout.cancel()
            self._testTimeout = None
        if self._underrunTimeout:
            self._debugger.ddebug("underrun: I already saw a recent underrun; ignoring")
        else:
            self._debugger.ddebug("underrun: scheduling 'restartSourceBin' in 2s")
            self._underrunTimeout = GObjectTimeout(2, self._restartSourceBin)
            self._underrunTimeout.start()
        self._debugger.ddebug("/onUnderrun")
    def _onRunning(self, element):
        """
        Cancel test_timeout as messages are obviously received on the bus.
        """
        self._debugger.ddebug("onRunning/")
        if self._testTimeout:
            self._testTimeout.cancel()
            self._testTimeout = None
        if self._underrunTimeout:
            self._debugger.ddebug("running: cancelling underrun timer")
            self._successiveUnderruns = 0
            self._underrunTimeout.cancel()
            self._underrunTimeout = None
        else:
            self._debugger.ddebug("running: no outstanding underrun timers; ignoring")
        self._debugger.ddebug("/onRunning")
    def _restartSourceBin(self):
        self._successiveUnderruns += 1
        if self._successiveUnderruns > 3:
            raise RuntimeError("Too many underruns.")
#            sys.stderr.write("Error: Video loss. Too many underruns.\n")
            sys.exit(1)
        gst.element_unlink_many(self._sourceBin, self._sinkBin)
        self._sourceBin.set_state(gst.STATE_NULL)
        self._sinkBin.set_state(gst.STATE_READY)
        self._pipeline.remove(self._sourceBin)
        self._sourceBin = None
        self._debug("Attempting to recover from video loss: Stopping source pipeline and waiting 5s...")
        time.sleep(5)
        self._debug("Restarting source pipeline...")
        self._sourceBin = self._createSourceBin()
        self._pipeline.add(self._sourceBin)
        gst.element_link_many(self._sourceBin, self._sinkBin)
        self._sourceBin.set_state(gst.STATE_PLAYING)
        self._sinkBin.set_state(gst.STATE_PLAYING)
        self._pipeline.set_state(gst.STATE_PLAYING)
        self._startTimestamp = None
        self._debug("Restarted source pipeline")
        self._underrunTimeout.start()
        # stop the timeout from running again
        return False
    def teardown(self):
        if self._pipeline:
            self._pipeline.remove(self._sourceBin)
            self._pipeline.remove(self._sinkBin)
            self._pipeline.send_event(gst.event_new_eos())
            self._pipeline.set_state(gst.STATE_NULL)
            self._pipeline = None
        if self._sourceBin:
            self._sourceBin.set_state(gst.STATE_NULL)
            self._sourceBin.remove_pad(self._pad)
            self._pad = None
            self._sourceBin = None
        if self._sinkBin:
            self._sinkBin.set_state(gst.STATE_NULL)
            self._sinkBin = None
