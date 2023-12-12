"""
Stream for capturing subprocess streams to a buffer.
"""

import threading
from io import StringIO
from typing import Any
import ctypes

# ignore E203
# flake8: noqa:E203


def _async_raise(tid, excobj):
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(excobj))
    if res == 0:
        raise ValueError("nonexistent thread id")
    if res > 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, 0)
        raise SystemError("PyThreadState_SetAsyncExc failed")


class StreamThread(threading.Thread):
    """Internal class for streaming subprocess streams to a buffer."""

    def __init__(self, in_stream: Any, out_stream: Any) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.dead = False
        self.in_stream = in_stream
        self.out_stream = out_stream
        self.buffer = StringIO()
        self.buffer_read_position = 0
        self.buffer_lock: threading.Lock = threading.Lock()
        self.start()

    def run(self) -> None:
        try:
            for line in iter(self.in_stream.readline, ""):
                with self.buffer_lock:
                    self.buffer.write(line)
        except KeyboardInterrupt:
            return

    def pump(self) -> None:
        """
        Pumps the supplied out_stream from the calling thread. Data
        is merged from this stream thread output process.
        """
        with self.buffer_lock:
            out = self.buffer.getvalue()
        if self.buffer_read_position == len(out):
            return
        out = out[self.buffer_read_position :]
        self.buffer_read_position += len(out)
        if self.out_stream:
            self.out_stream.write(out)

    def join_once(self) -> None:
        """Like join() but safe for multiple calls."""
        if not self.dead and self.is_alive():
            try:
                self.join(timeout=0.1)
                return
            except Exception:  # pylint: disable=broad-except
                try:
                    self.terminate()
                except Exception:  # pylint: disable=broad-except
                    pass

    def to_string(self) -> str:
        """Converts the whole buffer into a string."""
        with self.buffer_lock:
            out = self.buffer.getvalue()
        return out

    def raise_exc(self, excobj):
        """Raises an exception in the threads with id, tid"""
        assert self.is_alive(), "thread must be started"
        for tid, tobj in threading._active.items():  # pylint: disable=W0212
            if tobj is self:
                _async_raise(tid, excobj)
                return

    def terminate(self):
        """Terminates the thread."""
        # must raise the SystemExit type, instead of a SystemExit() instance
        # due to a bug in PyThreadState_SetAsyncExc
        self.raise_exc(SystemExit)
