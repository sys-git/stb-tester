'''
Created on 1 Nov 2012

@author: YouView
'''
import gst

def saveFrame(buf, filename):
    '''Save a gstreamer buffer to the specified file in png format.'''
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
