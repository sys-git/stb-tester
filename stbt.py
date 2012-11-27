from collections import namedtuple
import Queue
import errno
import inspect
import os
import re
import socket
import sys
import time
import unittest
import tempfile
import threading
import ConfigParser
import argparse
import nose
import pickle

class ArgvHider:
    """ For use with 'with' statement:  Unsets argv and resets it.

    This is used because otherwise gst-python will exit if '-h', '--help', '-v'
    or '--version' command line arguments are given.
    """
    def __enter__(self):
        self.argv = sys.argv[:]
        del sys.argv[1:]

    def __exit__(self, type, value, traceback):
        sys.argv = self.argv

with ArgvHider():
    import pygst  # gstreamer
    pygst.require("0.10")
    import gst
    import gobject
    import glib

# Functions available to stbt scripts
#===========================================================================

def press(key):
    """Send the specified key-press to the system under test.

    The mechanism used to send the key-press depends on what you've configured
    with `--control`.

    `key` is a string. The allowed values depend on the control you're using:
    If that's lirc, then `key` is a key name from your lirc config file.
    """
    global control
    return control.press(key)

class Position(namedtuple('Position', 'x y')):
    """
    * `x` and `y`: Integer coordinates from the top left corner of the video
      frame.
    """
    pass

class MatchResult(
    namedtuple('MatchResult', 'timestamp match position first_pass_result')):
    """
    * `timestamp`: Video stream timestamp.
    * `match`: Boolean result.
    * `position`: `Position` of the match.
    * `first_pass_result`: Value between 0 (poor) and 1.0 (excellent match)
      from the first pass of the two-pass templatematch algorithm.
    """
    pass

def detect_match(image, timeout_secs=10, noise_threshold=0.16):
    """Generator that yields a sequence of one `MatchResult` for each frame
    processed from the source video stream.

    Returns after `timeout_secs` seconds. (Note that the caller can also choose
    to stop iterating over this function's results at any time.)

    `noise_threshold` is a parameter used by the templatematch algorithm.
    Increase `noise_threshold` to avoid false negatives, at the risk of
    increasing false positives (a value of 1.0 will report a match every time).
    """

    params = {
        "template": findPath(image),
        "noiseThreshold": noise_threshold,
        }
    debug("Searching for " + params["template"])
    if not os.path.isfile(params["template"]):
        raise UITestError("No such template file: %s" % image)

    for message, buf in display.detect("template_match", params, timeout_secs):
        # Discard messages generated from previous call with different template
        if message["template_path"] == params["template"]:
            result = MatchResult(timestamp=buf.timestamp,
                match=message["match"],
                position=Position(message["x"], message["y"]),
                first_pass_result=message["first_pass_result"])
            debug("%s found: %s" % (
                  "Match" if result.match else "Weak match", str(result)))
            yield result

class MotionResult(namedtuple('MotionResult', 'timestamp motion')):
    """
    * `timestamp`: Video stream timestamp.
    * `motion`: Boolean result.
    """
    pass

def detect_motion(timeout_secs=10, noise_threshold=0.84, mask=None):
    """Generator that yields a sequence of one `MotionResult` for each frame
    processed from the source video stream.

    Returns after `timeout_secs` seconds. (Note that the caller can also choose
    to stop iterating over this function's results at any time.)

    `noise_threshold` is a parameter used by the motiondetect algorithm.
    Increase `noise_threshold` to avoid false negatives, at the risk of
    increasing false positives (a value of 0.0 will never report motion).
    This is particularly useful with noisy analogue video sources.

    `mask` is a black and white image that specifies which part of the image
    to search for motion. White pixels select the area to search; black pixels
    the area to ignore.
    """

    debug("Searching for motion")
    params = {
        "enabled": True,
        "noiseThreshold": noise_threshold,
        }
    if mask:
        params["mask"] = findPath(mask)
        debug("Using mask %s" % (params["mask"]))
        if not os.path.isfile(params["mask"]):
            debug("No such mask file: %s" % mask)
            raise UITestError("No such mask file: %s" % mask)

    for msg, buf in display.detect("motiondetect", params, timeout_secs):
        # Discard messages generated from previous calls with a different mask
        if ((mask and msg["masked"] and msg["mask_path"] == params["mask"])
                or (not mask and not msg["masked"])):
            result = MotionResult(timestamp=buf.timestamp,
                                  motion=msg["has_motion"])
            debug("%s detected. Timestamp: %d." %
                ("Motion" if result.motion else "No motion", result.timestamp))
            yield result

def wait_for_match(image, timeout_secs=10,
                   consecutive_matches=1, noise_threshold=0.16):
    """Search for `image` in the source video stream.

    Returns `MatchResult` when `image` is found.
    Raises `MatchTimeout` if no match is found after `timeout_secs` seconds.

    `consecutive_matches` forces this function to wait for several consecutive
    frames with a match found at the same x,y position.

    Increase `noise_threshold` to avoid false negatives, at the risk of
    increasing false positives (a value of 1.0 will report a match every time);
    increase `consecutive_matches` to avoid false positives due to noise. But
    please let us know if you are having trouble with image matches, so that we
    can improve the matching algorithm.
    """

    match_count = 0
    last_pos = Position(0, 0)
    for res in detect_match(image, timeout_secs, noise_threshold):
        if res.match and (match_count == 0 or res.position == last_pos):
            match_count += 1
        else:
            match_count = 0
        last_pos = res.position
        if match_count == consecutive_matches:
            debug("Matched " + image)
            return res

    screenshot = display.captureScreenshot()
    raise MatchTimeout(screenshot, image, timeout_secs)

def press_until_match(key, image,
                      interval_secs=3, noise_threshold=0.16, max_presses=10):
    """Calls `press` as many times as necessary to find the specified `image`.

    Returns `MatchResult` when `image` is found.
    Raises `MatchTimeout` if no match is found after `max_presses` times.

    `interval_secs` is the number of seconds to wait for a match before
    pressing again.
    """
    i = 0
    while True:
        try:
            return wait_for_match(image, timeout_secs=interval_secs,
                                  noise_threshold=noise_threshold)
        except MatchTimeout:
            if i < max_presses:
                press(key)
                i += 1
            else:
                raise

def wait_for_motion(timeout_secs=10, consecutive_frames=10,
        noise_threshold=0.84, mask=None):
    """Search for motion in the source video stream.

    Returns `MotionResult` when motion is detected.
    Raises `MotionTimeout` if no motion is detected after `timeout_secs`
    seconds.

    Considers the video stream to have motion if there were differences between
    10 consecutive frames (or the number specified with `consecutive_frames`).

    Increase `noise_threshold` to avoid false negatives, at the risk of
    increasing false positives (a value of 0.0 will never report motion).
    This is particularly useful with noisy analogue video sources.

    `mask` is a black and white image that specifies which part of the image
    to search for motion. White pixels select the area to search; black pixels
    the area to ignore.
    """
    debug("Waiting for %d consecutive frames with motion" % consecutive_frames)
    consecutive_frames_count = 0
    for res in detect_motion(timeout_secs, noise_threshold, mask):
        if res.motion:
            consecutive_frames_count += 1
        else:
            consecutive_frames_count = 0
        if consecutive_frames_count == consecutive_frames:
            debug("Motion detected.")
            return res

    screenshot = display.captureScreenshot()
    raise MotionTimeout(screenshot, mask, timeout_secs)

def argParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--control',
        help='The remote control to control the stb (default: %(default)s)')
    parser.add_argument('--source-pipeline',
        help='A gstreamer pipeline to use for A/V input (default: '
             '%(default)s)')
    parser.add_argument('--sink-pipeline',
        help='A gstreamer pipeline to use for video output '
             '(default: %(default)s)')

    class IncreaseDebugLevel(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            global _debug_level
            _debug_level += 1
            setattr(namespace, self.dest, _debug_level)

    global _debug_level
    _debug_level = 0
    parser.add_argument('-v', '--verbose', action=IncreaseDebugLevel, nargs=0,
        help='Enable debug output (specify twice to enable GStreamer element '
             'dumps to ./stbt-debug directory)')

    return parser

def saveFrame(buf, filename):
    """Save a GStreamer buffer to the specified file in png format.

    Takes a buffer `buf` obtained from `getFrame` or from the `screenshot`
    property of `MatchTimeout` or `MotionTimeout`.
    """
    pipeline = gst.parse_launch(" ! ".join([
                'appsrc name="src" caps="%s"' % buf.get_caps(),
                'ffmpegcolorspace',
                'pngenc',
                'filesink location="%s"' % filename,
                ]))
    src = pipeline.get_by_name("src")
    # This is actually a (synchronous) method call to push-buffer:
    src.emit('push-buffer', buf)
    src.emit('end-of-stream')
    pipeline.set_state(gst.STATE_PLAYING)
    msg = pipeline.get_bus().poll(
        gst.MESSAGE_ERROR | gst.MESSAGE_EOS, 25 * gst.SECOND)
    pipeline.set_state(gst.STATE_NULL)
    if msg.type == gst.MESSAGE_ERROR:
        err, dbg = msg.parse_error()
        raise RuntimeError("%s: %s\n%s\n" % (err, err.message, dbg))

def getFrame():
    """Get a GStreamer buffer containing the current video frame."""
    return display.captureScreenshot()

def debug(s):
    """Print the given string to stderr if stbt run `--verbose` was given."""
    if _debug_level > 0:
        sys.stderr.write("%s: %s\n" % (os.path.basename(sys.argv[0]), str(s)))

class Debugger(object):
    """
    Single output sink for all application logging.
    """
    def __init__(self, level):
        self._debugLevel = level
    def level(self):
        return self._debugLevel
    def debug(self, s):
        if self._debugLevel > 0:
            sys.stderr.write("%s: %s\n"%(os.path.basename(sys.argv[0]), str(s)))
    def ddebug(self, s):
        """Extra verbose debug for stbt developers, not end users"""
        if self._debugLevel > 1:
            sys.stderr.write("%s: %s\n"%(os.path.basename(sys.argv[0]), str(s)))
    def warn(self, s):
        sys.stderr.write("%s: warning: %s\n"%(os.path.basename(sys.argv[0]), str(s)))
    def error(self, s):
        sys.stderr.write("%s: error: %s\n"%(os.path.basename(sys.argv[0]), str(s)))

global _debug_level
_debug_level = 0
debugger = Debugger(_debug_level)
_mainloop = glib.MainLoop()     #@UndefinedVariable

class UITestError(Exception):
    """The test script had an unrecoverable error."""
    pass

class UIControlFailure(UITestError):
    pass

class UITestFailure(Exception):
    """The test failed because the system under test didn't behave as expected.
    """
    pass

class MatchTimeout(UITestFailure):
    """
    * `screenshot`: A GStreamer frame from the source video when the search
      for the expected image timed out.
    * `expected`: Filename of the image that was being searched for.
    * `timeout_secs`: Number of seconds that the image was searched for.
    """
    def __init__(self, screenshot, expected, timeout_secs):
        self.screenshot = screenshot
        self.expected = expected
        self.timeout_secs = timeout_secs

class MotionTimeout(UITestFailure):
    """
    * `screenshot`: A GStreamer frame from the source video when the search
      for motion timed out.
    * `mask`: Filename of the mask that was used (see `wait_for_motion`).
    * `timeout_secs`: Number of seconds that motion was searched for.
    """
    def __init__(self, screenshot, mask, timeout_secs):
        self.screenshot = screenshot
        self.mask = mask
        self.timeout_secs = timeout_secs

class ConfigurationError(UITestError):
    pass


# stbt-run initialisation and convenience functions
# (you will need these if writing your own version of stbt-run)
#===========================================================================

# Internal
#===========================================================================

def MessageIterator(bus, signal, mainloop, checkAborted=lambda: False):
    queue = Queue.Queue()
    def sig(bus, message):
        queue.put(message)
        mainloop.quit()
    bus.connect(signal, sig)
    try:
        while not checkAborted():
            mainloop.run()
            # Check what interrupted the main loop (new message, error thrown)
            try:
                item = queue.get(block=False)
                yield item
            except Queue.Empty:
                checkAborted = lambda: True
    finally:
        bus.disconnect_by_func(sig)

class BaseDisplay(object):
    def __init__(self, debugger, getWindowId):
        self._debugger = debugger
        self._getWindowId = getWindowId
        self._pipeline = None
        self._screenshot = None
    def _setPipeline(self, pipeline):
        self._pipeline = pipeline
    def getPipeline(self):
        return self._pipeline
    def getWindowId(self):
        if self._getWindowId!=None:
            return self._getWindowId()
    def _setScreenshot(self, screenshot):
        self._screenshot = screenshot
    def getScreenshot(self):
        return self._screenshot

class RecorderDisplay(BaseDisplay):
    def __init__(self, videoSource, videoSink, debugger, windowId=None):
        super(RecorderDisplay, self).__init__(debugger, windowId)
        pipe = " ".join([
                videoSource,
                " ! tee name=t",
                " t. ! queue leaky=2",
                "    ! ffmpegcolorspace",
                "    ! appsink name=screenshot max-buffers=1 drop=true "
                        "sync=false caps=video/x-raw-rgb",
                " t. ! queue leaky=2 ! ffmpegcolorspace ! ", videoSink
                ])
        self._setPipeline(gst.parse_launch(pipe))
        self._screenshot = self._pipeline.get_by_name("screenshot")
        self._pipeline.get_bus().connect("message::error", self.on_error)
        self._pipeline.get_bus().connect("message::warning", self.on_warning)
        self._pipeline.set_state(gst.STATE_PLAYING)
    def on_error(self, bus, message):
        assert message.type==gst.MESSAGE_ERROR
        err, dbg = message.parse_error()
        self._debugger.error("Error: %s: %s\n%s\n"%(err, err.message, dbg))
        sys.exit(1)
    def on_warning(self, bus, message):
        assert message.type == gst.MESSAGE_WARNING
        err, dbg = message.parse_warning()
        self._debugger.warn("Warning: %s: %s\n%s\n"%(err, err.message, dbg))

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
            if _mkdir("stbt-debug/motiondetect") and _mkdir(
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
        print ">> detect <<"
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
                startTimestamp = None
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
                        if not startTimestamp:
                            startTimestamp = buf.timestamp
                        try:
                            if ((buf.timestamp-startTimestamp) > (timeoutSecs*100000000000)):
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
        self._pipeline.set_state(gst.STATE_PLAYING)
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

class GObjectTimeout:
    """Responsible for setting a timeout in the GTK main loop.

    Can be used as a Context Manager in a 'with' statement.
    """
    def __init__(self, timeout_secs, handler, *args):
        self.timeout_secs = timeout_secs
        self.handler = handler
        self.args = args
        self.timeout_id = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.cancel()

    def start(self):
        self.timeout_id = gobject.timeout_add(
            self.timeout_secs * 1000, self.handler, *self.args)

    def cancel(self):
        if self.timeout_id:
            gobject.source_remove(self.timeout_id)
        self.timeout_id = None

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
        raise ConfigurationError('Invalid remote control URI: "%s"'%uri)

class BaseRemote(object):
    def __init__(self, debugger):
        self._debugger = debugger
    def teardown(self):
        r"""
        Override this as necessary.
        """
        pass

class NullRemote(BaseRemote):
    def press(self, key):
        debug('NullRemote: Ignoring request to press "%s"' % key)

class TestRemote(BaseRemote):
    """
    Remote control used by tests.
    Changes the videotestsrc image to the specified pattern ("0" to "20").
    See `gst-inspect videotestsrc`.
    """
    def __init__(self, display, debugger):
        super(TestRemote, self).__init__(debugger)
        self._display = display
        count = -1
        videoSrc = None
        while videoSrc==None and count<1:
            count += 1
            videoSrc = display.getPipeline().get_by_name("videotestsrc%(C)s"%{"C":count})
        print "Found on count: %(C)s"%{"C":count}
        self._videoSrc = videoSrc
        if not self._videoSrc:
            raise ConfigurationError('The "test" control can only be used'
                                     'with source-pipeline = "videotestsrc"')
    def press(self, key):
        if key not in [str(x) for x in range(21)]:
            raise UIControlFailure('Key "%s" not valid for the "test" control'
                                ' (only "0" to "20" allowed)'%key)
        self._videoSrc.props.pattern = int(key)
        self._debugger.debug("Pressed " + key)
    def teardown(self):
        if self._videoSrc:
            self._videoSrc.send_event(gst.event_new_eos())
            self._videoSrc.set_state(gst.STATE_NULL)
            self._videoSrc = None
            pass

class VirtualRemote(BaseRemote):
    """
    Send a key-press to a set-top box running a VirtualRemote listener.
    control = VirtualRemote("192.168.0.123")
    control.press("MENU")
    """
    CONNECT_TIMEOUT = 3
    def __init__(self, hostname, port, debugger):
        super(VirtualRemote, self).__init__(debugger)
        self._sock = socket.socket()
        self._debugger.debug("VirtualRemote: Connecting to %s:%d"%(hostname, port))
        try:
            self._sock.settimeout(VirtualRemote.CONNECT_TIMEOUT)
            self._sock.connect((hostname, port))
            self._sock.settimeout(None)
            self._debugger.debug("VirtualRemote: Connected to %s:%d"%(hostname, port))
        except socket.error as e:
            e.args = (("Failed to connect to VirtualRemote at %s:%d: %s"%(hostname, port, e)),)
            e.strerror = e.args[0]
            raise
    def press(self, key):
        self._sock.send("D\t%s\n\0U\t%s\n\0"%(key, key))  # key Down, then key Up
        self._debugger.debug("Pressed "+key)
    def close(self):
        self._sock.close()
        self._sock = None
    @staticmethod
    def listen(address, port, debugger):
        """
        Waits for a VirtualRemote to connect, and returns an iterator yielding
        keypresses."""
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind((address, port))
        serversocket.listen(5)
        debugger.debug("Waiting for connection from virtual remote control "
                         "on %s:%d...\n" % (address, port))
        (connection, address) = serversocket.accept()
        debugger.debug("Accepted connection from %s\n" % str(address))
        return VirtualRemote.keyReader(VirtualRemote.readRecords(connection, '\n\0'))
    @staticmethod
    def keyReader(cmdIter):
        r"""
        Converts virtual remote records into list of keypresses
        >>> list(vr_key_reader(['D\tHELLO', 'U\tHELLO']))
        ['HELLO']
        >>> list(vr_key_reader(['D\tCHEESE', 'D\tHELLO', 'U\tHELLO', 'U\tCHEESE']))
        ['HELLO', 'CHEESE']
        """
        for i in cmdIter:
            (action, key) = i.split('\t')
            if action=='U':
                yield key
    @staticmethod
    def readRecords(stream, sep):
        r"""
        Generator that splits stream into records given a separator
        >>> import StringIO
        >>> s = StringIO.StringIO('hello\n\0This\n\0is\n\0a\n\0test\n\0')
        >>> list(read_records(FileToSocket(s), '\n\0'))
        ['hello', 'This', 'is', 'a', 'test']
        """
        buf = ""
        while True:
            s = stream.recv(4096)
            if len(s) == 0:
                break
            buf += s
            cmds = buf.split(sep)
            buf = cmds[-1]
            for i in cmds[:-1]:
                yield i

class LircRemote(BaseRemote):
    """
    Send a key-press via a LIRC-enabled infrared blaster.
    See http://www.lirc.org/html/technical.html#applications
    """
    CONNECT_TIMEOUT = 3
    def __init__(self, lircdSocket, controlName, debugger):
        super(LircRemote, self).__init__(debugger)
        self._controlName = controlName
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._debugger.debug("LircRemote: Connecting to %s" % lircdSocket)
        try:
            self._sock.settimeout(LircRemote.CONNECT_TIMEOUT)
            self._sock.connect(lircdSocket)
            self._sock.settimeout(None)
            self._debugger.debug("LircRemote: Connected to %s" % lircdSocket)
        except socket.error as e:
            e.args = (("Failed to connect to Lirc socket %s: %s"%(lircdSocket, e)),)
            e.strerror = e.args[0]
            raise
    def press(self, key):
        self._sock.send("SEND_ONCE %s %s\n"%(self._controlName, key))
        self._debugger.debug("Pressed " + key)
    def close(self):
        self._sock.close()
        self._sock = None
    @staticmethod
    def listen(lircdSocket, controlName, debugger):
        """
        Returns an iterator yielding key presses received from lircd.

        See http://www.lirc.org/html/technical.html#applications
        """
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        debugger.debug("control-recorder connecting to lirc socket '%s'..." % lircdSocket)
        sock.connect(lircdSocket)
        debugger.debug("control-recorder connected to lirc socket")
        return LircRemote.keyreader(sock.makefile(), controlName, debugger)
    @staticmethod
    def keyreader(cmdIter, controlName, debugger):
        r"""
        Convert lircd messages into list of keypresses

        >>> list(lirc_key_reader(['0000dead 00 MENU My-IR-remote',
        ...                       '0000beef 00 OK My-IR-remote',
        ...                       '0000f00b 01 OK My-IR-remote',
        ...                       'BEGIN', 'SIGHUP', 'END'],
        ...                      'My-IR-remote'))
        ['MENU', 'OK']
        """
        for s in cmdIter:
            debugger.debug("lirc_key_reader received: %s" % s.rstrip())
            m = re.match(r"\w+ (?P<repeat_count>\d+) (?P<key>\w+) %s"%controlName,s)
            if m and int(m.group('repeat_count'))==0:
                yield m.group('key')

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

class FileRemote(BaseRemote):
    @staticmethod
    def listen(filename, debugger):
        """
        @summary: A generator that returns lines from the file given by filename.
        
        Unfortunately treating a file as a iterator doesn't work in the case of
        interactive input, even when we provide bufsize=1 (line buffered) to the
        call to open() so we have to have this function to work around it.
        """
        f = open(filename, 'r')
        if filename == '/dev/stdin':
            debugger.debug('Waiting for keypresses from standard input...\n')
        while True:
            line = f.readline()
            if line == '':
                f.close()
                raise StopIteration
            yield line.rstrip()

def loadDefaultArgs(tool):
    conffile = ConfigParser.SafeConfigParser()
    conffile.add_section('global')
    conffile.add_section(tool)

    # When run from the installed location (as `stbt run`), will read config
    # from $SYSCONFDIR/stbt/stbt.conf (see `stbt.in`); when run from the source
    # directory (as `stbt-run`) will read config from the source directory.
    system_config = os.environ.get(
        'STBT_SYSTEM_CONFIG',
        os.path.join(os.path.dirname(__file__), 'stbt.conf'))

    files_read = conffile.read([
        system_config,
        # User config: ~/.config/stbt/stbt.conf, as per freedesktop's base
        # directory specification:
        '%s/stbt/stbt.conf' % os.environ.get('XDG_CONFIG_HOME',
                                            '%s/.config' % os.environ['HOME']),
        # Config files specific to the test suite / test run:
        os.environ.get('STBT_CONFIG_FILE', ''),
        ])
    assert(system_config in files_read)
    return dict(conffile.items('global'), **dict(conffile.items(tool)))

def findPath(image):
    """Searches for the given filename and returns the full path.

    Searches in the directory of the script that called (for example)
    detect_match, then in the directory of that script's caller, etc.
    """

    if os.path.isabs(image):
        return image

    # stack()[0] is _find_path;
    # stack()[1] is _find_path's caller, e.g. detect_match;
    # stack()[2] is detect_match's caller (the user script).
    for caller in inspect.stack()[2:]:
        caller_image = os.path.join(
            os.path.dirname(inspect.getframeinfo(caller[0]).filename),
            image)
        if os.path.isfile(caller_image):
            return os.path.abspath(caller_image)

    # Fall back to image from cwd, for convenience of the selftests
    return os.path.abspath(image)

def _mkdir(d):
    try:
        os.makedirs(d)
    except OSError, e:
        if e.errno != errno.EEXIST:
            return False
    return os.path.isdir(d) and os.access(d, os.R_OK | os.W_OK)

def ddebug(s):
    """Extra verbose debug for stbt developers, not end users"""
    if _debug_level > 1:
        sys.stderr.write("%s: %s\n" % (os.path.basename(sys.argv[0]), str(s)))

def warn(s):
    sys.stderr.write("%s: warning: %s\n" % (
            os.path.basename(sys.argv[0]), str(s)))

# Tests
#===========================================================================

class FileToSocket:
    """Makes something File-like behave like a Socket for testing purposes

    >>> import StringIO
    >>> s = FileToSocket(StringIO.StringIO("Hello"))
    >>> s.recv(3)
    'Hel'
    >>> s.recv(3)
    'lo'
    """
    def __init__(self, f):
        self.file = f

    def recv(self, bufsize, flags=0):
        return self.file.read(bufsize)

def FakeLircd(address):
    # This needs to accept 2 connections (from LircRemote and
    # lirc_remote_listen) and, on receiving input from the LircRemote
    # connection, write to the lirc_remote_listen connection.
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.bind(address)
    s.listen(5)
    listener, _ = s.accept()
    control, _ = s.accept()
    for cmd in control.makefile():
        m = re.match(r'SEND_ONCE (?P<control>\w+) (?P<key>\w+)', cmd)
        if m:
            d = m.groupdict()
            listener.send('00000000 0 %s %s\n' % (d['key'], d['control']))

class Test(unittest.TestCase):
    def setUp(self):
        self._debugger = Debugger(level=2)
    def test_that_lirc_remote_is_symmetric_with_lirc_remote_listen(self):
        lircd_socket = tempfile.mktemp()
        t = threading.Thread()
        t.run = lambda: FakeLircd(lircd_socket)
        t.start()
        time.sleep(0.01)  # Give it a chance to start listening (sorry)
        listener = LircRemote.listen(lircd_socket, 'test', self._debugger)
        control = LircRemote(lircd_socket, 'test', self._debugger)
        for i in ['DOWN', 'DOWN', 'UP', 'GOODBYE']:
            control.press(i)
            assert listener.next() == i
        control.close()
        t.join()
    def test_that_virtual_remote_is_symmetric_with_virtual_remote_listen(self):
        t = threading.Thread()
        vrl = []
        t.run = lambda: vrl.append(VirtualRemote.listen('localhost', 2033, self._debugger))
        t.start()
        time.sleep(0.01)  # Give it a chance to start listening (sorry)
        vr = VirtualRemote('localhost', 2033, self._debugger)
        t.join()
        for i in ['DOWN', 'DOWN', 'UP', 'GOODBYE']:
            vr.press(i)
        vr.close()
        assert list(vrl[0]) == ['DOWN', 'DOWN', 'UP', 'GOODBYE']

class TVector(object):
    def __init__(self, methodName=None, moduleSig=None, filename=None, root=None):
        self._methodName = methodName
        self._moduleSig = moduleSig
        self._filename = filename
        self._root = root
    def methodName(self, defaultValue=None):
        if self._methodName==None:
            return defaultValue
        return self._methodName
    def moduleSig(self):
        return self._moduleSig
    def filename(self):
        return self._filename
    def root(self):
        return self._root
    def __str__(self):
        if self._methodName!=None:
#            if self._methodName.find(".")==-1:
#                return "%(F)s.%(M)s"%{"F":self.getRelModule(), "M":self._methodName}
            return "%(F)s:%(M)s"%{"F":self.getRelPath(), "M":self._methodName}
        return self.getRelPath()
    def getRelPath(self):
        return self._filename.partition(self._root+os.sep)[2]
    def getRelModule(self):
        p = self.getRelPath()
        name = os.path.splitext(os.path.basename(p))[0]
        dirname = os.path.dirname(p)
        return dirname+"."+name

def discover(args):
    result = []
    if args.nose==True:
        #    Now use nose to 'discover' tests:
        oldcwd = os.getcwd()
        try:
            testRoot = args.script_root
            sys.path.append(testRoot)
            tmpFile = os.path.realpath("test_cases.txt")
            cargs=["", "-v" , "--collect-only", "--exe", "--with-id", "--id-file=%(F)s"%{"F":tmpFile}]
            try:
                result = nose.run(defaultTest=testRoot, argv=cargs)
            except Exception, _e:
                pass
            else:
                if result is True:
                    args.script = []
                    #    Now query the selector:
                    s = pickle.loads(file(tmpFile).read())["ids"]
                    if os.path.exists(tmpFile):
                        os.remove(tmpFile)
                    for testCase in s.values():
                        filepath, relativeModuleSignature, test = testCase
                        testPath = filepath.strip()
                        if test is not None:
                            testName = test.strip()
                            #    Now we have: testPath, relativeModuleSignature, test
                            args.script.append(TVector(filename=testPath, moduleSig=relativeModuleSignature, methodName=testName, root=args.script_root))
        finally:
            os.chdir(oldcwd)
    return result

class Command(object):
    def __init__(self, cmd, uId, data=None):
        self.cmd = cmd
        self.uId = uId
        self.data = data

class TRCommands(object):
    TEARDOWN = "teardown()"
    RUN = "run()"
    RUNNING_START = "running-start()"
    RUNNING_FINISHED = "running-finished()"
    RAN = "ran()"
    RESULT = "result()"
    STEP = "step()"
    STALL = "stall()"

class BaseResult(object):
    pass

class NoResult(BaseResult):
    def __str__(self):
        return "NoResult"

class Result(BaseResult):
    OK = "no exception"
    def __init__(self, result):
        super(Result, self).__init__()
        self._result = result
    def result(self):
        return self._result
    def __str__(self):
        return "Result: %(T)s( %(R)s )"%{"T": type(self._result), "R":self._result}
