"""
Stream for capturing subprocess streams to a buffer.
"""

import threading
from io import StringIO
from typing import Any

# ignore E203
# flake8: noqa:E203

THREAD_JOIN_TIMEOUT = 5

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

    def join_once(self) -> Any:
        """Like join() but safe for multiple calls."""
        if not self.dead:
            self.dead = True
            self.join(timeout=THREAD_JOIN_TIMEOUT)

    def to_string(self) -> str:
        """Converts the whole buffer into a string."""
        with self.buffer_lock:
            out = self.buffer.getvalue()
        return out
