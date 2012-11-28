'''
Created on 1 Nov 2012

@author: YouView
'''

from StbTester.core.display.BaseDisplay import BaseDisplay
import gst
import sys

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
