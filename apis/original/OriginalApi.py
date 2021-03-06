'''
Created on 31 Oct 2012

@author: YouView
'''

from MatchResult import MatchResult
from MatchTimeout import MatchTimeout
from MotionResult import MotionResult
from MotionTimeout import MotionTimeout
from Position import Position
from StbTester.apis.impls.common.errors.ScriptApiParamError import \
    ScriptApiParamError
from StbTester.apis.impls.common.errors.UITestError import UITestError
from StbTester.core.errors.ConfigurationError import ConfigurationError
from StbTester.core.utils.PathUtils import findPath
from collections import deque
import os

class TheApi(object):
    r"""
    @attention: A class not inheriting from BaseApi MUST be a new-style class
    (ie: inherit from 'object').
    @attention: The class MUST implement the following attributes: ['NAMESPACE',
    'NAME', 'VERSION'] but need not implement __init__. If it does implement
    __init__ then it MUST call super(classname, self).__init__(...).
    @attention: Follow the rules for naming api methods - see BaseApi:
    """
    NAMESPACE = "Fred"      #    The default namespace for the api, ie: namespace.methodname(params)
    NAME = "original-stbtester-api"
    VERSION = 1.0
    def __init__(self, control, display, srcPath, debugger):
        super(TheApi, self).__init__(control, display, srcPath, debugger)
        #    Do more stuff in here as required.
        pass
    def press(self, key):
        """
        Send the specified key-self.press to the system under test.
    
        The mechanism used to send the key-self.press depends on what you've configured
        with `--control`.
    
        `key` is a string. The allowed values depend on the control you're using:
        If that's lirc, then `key` is a key name from your lirc config file.
        """
        if key==None:
            raise ScriptApiParamError("press", "key", key)
        return self._control.press(key)
    def detect_match(self, image, timeout_secs=10, noise_threshold=0.16):
        """
        Generator that yields a sequence of one `MatchResult` for each frame in
        the source video stream.
    
        Returns after `timeout_secs` seconds. (Note that the caller can also choose
        to stop iterating over this function's results at any time.)
    
        `noise_threshold` is a parameter used by the templatematch algorithm.
        Increase `noise_threshold` to avoid false negatives, at the risk of
        increasing false positives (a value of 1.0 will report a match every time).
        """
        if not isinstance(timeout_secs, (int, float, long)):
            raise ScriptApiParamError("detect_match", "timeout_secs", timeout_secs, tuple(int, float, long))
        if not isinstance(noise_threshold, float):
            raise ScriptApiParamError("detect_match", "noise_threshold", noise_threshold, tuple(float))
        params = {
            "template": findPath(image),
            "noiseThreshold": noise_threshold,
            }
        self._debugger.debug("Searching for " + params["template"])
        if not os.path.isfile(params["template"]):
            raise UITestError("No such template file: %s" % image)
        for message, buf in self._display.detect("template_match", params, timeout_secs, self.checkAborted):
            self.checkAborted()
            # Discard messages generated from previous call with different template
            if message["template_path"]==params["template"]:
                result = MatchResult(timestamp=buf.timestamp,
                                     match=message["match"],
                                     position=Position(message["x"], message["y"]),
                                     first_pass_result=message["first_pass_result"])
                self._debugger.debug("%s found: %s" % (
                      "Match" if result.match else "Weak match", str(result)))
                yield result
    def detect_motion(self, timeout_secs=10, noise_threshold=0.84, mask=None):
        """
        Generator that yields a sequence of one `MotionResult` for each frame
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
        if not isinstance(timeout_secs, (int, float, long)):
            raise ScriptApiParamError("detect_motion", "timeout_secs", timeout_secs, tuple(int, float, long))
        self._debugger.debug("Searching for motion")
        params = {
            "enabled": True,
            "noiseThreshold": noise_threshold,
        }
        if mask:
            params["mask"] = findPath(mask)
            self._debugger.debug("Using mask %s" % (params["mask"]))
            if not os.path.isfile(params["mask"]):
                self._debugger.debug("No such mask file: %s"%mask)
                raise UITestError("No such mask file: %s"%mask)
        for msg, buf in self._display.detect("motiondetect", params, timeout_secs):
            self.checkAborted()
            # Discard messages generated from previous calls with a different mask
            if ((mask and msg["masked"] and msg["mask_path"] == params["mask"])
                    or (not mask and not msg["masked"])):
                result = MotionResult(timestamp=buf.timestamp, motion=msg["has_motion"])
                self._debugger.debug("%s detected. Timestamp: %d."%
                    ("Motion" if result.motion else "No motion", result.timestamp))
                yield result
    def wait_for_match(self, image, timeout_secs=10, consecutive_matches=1, noise_threshold=0.16):
        """
        Search for `image` in the source video stream.
    
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
        if not isinstance(timeout_secs, (int, float, long)):
            raise ScriptApiParamError("wait_for_match", "timeout_secs", timeout_secs, tuple(int, float, long))
        if not isinstance(noise_threshold, float):
            raise ScriptApiParamError("wait_for_match", "noise_threshold", noise_threshold, tuple(float))
        if not isinstance(consecutive_matches, int):
            raise ScriptApiParamError("wait_for_match", "consecutive_matches", consecutive_matches, tuple(int))
        matchCount = 0
        lastPos = Position(0, 0)
        for res in self.detect_match(image, timeout_secs, noise_threshold):
            self.checkAborted()
            if res.match and ((matchCount==0) or (res.position==lastPos)):
                matchCount += 1
            else:
                matchCount = 0
            lastPos = res.position
            if matchCount==consecutive_matches:
                self._debugger.debug("Matched " + image)
                return res
        screenshot = self._display.captureScreenshot()
        raise MatchTimeout(screenshot, image, timeout_secs)
    def press_until_match(self, key, image, interval_secs=3, noise_threshold=0.16, max_presses=10):
        """
        Calls `self.press` as many times as necessary to find the specified `image`.
    
        Raises `MatchTimeout` if no match is found after `max_presses` times.
    
        `interval_secs` is the number of seconds to wait for a match before
        pressing again.
        """
        if not isinstance(interval_secs, (int, float, long)):
            raise ScriptApiParamError("press_until_match", "interval_secs", interval_secs, tuple(int, float, long))
        if not isinstance(noise_threshold, float):
            raise ScriptApiParamError("press_until_match", "noise_threshold", noise_threshold, tuple(float))
        if not isinstance(max_presses, int):
            raise ScriptApiParamError("press_until_match", "max_presses", max_presses, tuple(int))
        i = 0
        while True:
            try:
                self.checkAborted()
                return self.wait_for_match(image, timeout_secs=interval_secs, noise_threshold=noise_threshold)
            except MatchTimeout, _e:
                if i<max_presses:
                    self.press(key)
                    i += 1
                else:
                    raise
    def wait_for_motion(self, timeout_secs=10, consecutive_frames=10, noise_threshold=0.84, mask=None):
        """
        Search for motion in the source video stream.
    
        Returns `MotionResult` when motion is detected.
        Raises `MotionTimeout` if no motion is detected after `timeout_secs`
        seconds.
    
        Considers the video stream to have motion if there were diferences between
        10 consecutive frames, or the number specified by `consecutive_frames`,
        which can be:
    
        * a positive integer value, or
        * a string in the form "x/y", where `x` is the number of frames with motion
          detected out of a sliding window of `y` frames.
    
        Increase `noise_threshold` to avoid false negatives, at the risk of
        increasing false positives (a value of 0.0 will never report motion).
        This is particularly useful with noisy analogue video sources.
    
        `mask` is a black and white image that specifies which part of the image
        to search for motion. White pixels select the area to search; black pixels
        the area to ignore.
        """
        if not isinstance(timeout_secs, (int, float, long)):
            raise ScriptApiParamError("wait_for_motion", "timeout_secs", timeout_secs, tuple(int, float, long))
        if not isinstance(consecutive_frames, int):
            raise ScriptApiParamError("wait_for_motion", "consecutive_frames", consecutive_frames, tuple(int))
        consecutive_frames = str(consecutive_frames)
        if '/' in consecutive_frames:
            motion_frames = int(consecutive_frames.split('/')[0])
            considered_frames = int(consecutive_frames.split('/')[1])
        else:
            motion_frames = int(consecutive_frames)
            considered_frames = int(consecutive_frames)
    
        if motion_frames > considered_frames:
            raise ConfigurationError(
                "`motion_frames` exceeds `considered_frames`")
    
        self._debugger.debug("Waiting for %d out of %d frames with motion" % (
            motion_frames, considered_frames))
    
        matches = deque(maxlen=considered_frames)
        for res in self.detect_motion(timeout_secs, noise_threshold, mask):
            matches.append(res.motion)
            if matches.count(True) >= motion_frames:
                self._debugger.debug("Motion detected.")
                return res

        screenshot = self._display.capture_screenshot()
        raise MotionTimeout(screenshot, mask, timeout_secs)

