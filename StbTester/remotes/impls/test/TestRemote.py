'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.apis.impls.common.errors.UIControlFailure import UIControlFailure
from StbTester.core.errors.ConfigurationError import ConfigurationError
from StbTester.remotes.impls.BaseRemote import BaseRemote
import gst

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
        self._debugger.debug("Found on count: %(C)s"%{"C":count})
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
