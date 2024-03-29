"""
Stream for capturing subprocess streams to a buffer.
"""

import ctypes
import threading
import traceback
import warnings
from typing import Any

# ignore E203
# flake8: noqa:E203

MAX_BUFFER_SIZE = 1024 * 1024 * 1  # 1MB


def _async_raise(tid, excobj):
    """Raises an exception in the threads with id, tid"""
    warnings.warn(f"async_raise: {tid}, {excobj}")
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

    def __init__(self, in_stream: Any, out_stream: Any, buffer_size: int) -> None:
        threading.Thread.__init__(self, daemon=True)
        self.dead = False
        self.in_stream = in_stream
        self.out_stream = out_stream
        self.buffer = ""
        self.buffer_read_position = 0
        self.buffer_lock: threading.Lock = threading.Lock()
        self.buffer_size = buffer_size
        self.final_string = ""
        self.start()

    def run(self) -> None:
        try:
            iter_lines = iter(self.in_stream.readline, b"")
            while True:
                line: str | None = None
                try:
                    line = next(iter_lines)
                    if not line:
                        break
                    with self.buffer_lock:
                        self.buffer += line
                except Exception as exc:  # pylint: disable=broad-except
                    stacktrace = traceback.format_exc()
                    warnings.warn(f"StreamThread exception: {exc}, {stacktrace}")
                    continue
        except KeyboardInterrupt:
            return
        except Exception as exc:  # pylint: disable=broad-except
            stacktrace = traceback.format_exc()
            warnings.warn(f"StreamThread exception: {exc}, {stacktrace}")

    def pump(self, ignore_dead_signal=False) -> None:
        """
        Pumps the supplied out_stream from the calling thread. Data
        is merged from this stream thread output process.
        """
        with self.buffer_lock:
            if self.dead and not ignore_dead_signal:
                return
            full_buffer = self.buffer
            out = full_buffer[self.buffer_read_position :]
            if not out:
                return
            self.buffer_read_position += len(out)
            if len(full_buffer) > self.buffer_size:
                to_remove = len(full_buffer) - self.buffer_size
                to_remove += int(0.25 * self.buffer_size)
                to_remove = max(0, to_remove)
                assert (
                    to_remove > 0
                ), f"unexpected, to_remove={to_remove} and should be > 0"
                self.buffer = full_buffer[to_remove:]
                self.buffer_read_position -= to_remove
        self.buffer_read_position += len(out)
        if self.out_stream:
            self.out_stream.write(out)

    def join_once(self) -> None:
        """Like join() but safe for multiple calls."""
        if not self.dead and self.is_alive():
            try:
                self.join(timeout=5.0)
                self.dead = True
                self.pump(ignore_dead_signal=True)
                self.final_string = self.to_string()
                return
            except Exception:  # pylint: disable=broad-except
                try:
                    self.terminate()
                except Exception:  # pylint: disable=broad-except
                    pass

    def to_string(self) -> str:
        """Converts the whole buffer into a string."""
        with self.buffer_lock:
            out = self.buffer
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

    def __del__(self):
        pass
