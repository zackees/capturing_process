# flake8: noqa: E501

import subprocess
import threading
import unittest
from io import StringIO
from typing import List

from capturing_process import CapturingProcess


class FakeStream:
    def __init__(self) -> None:
        self.buff: List[str] = []

    def write(self, data: str) -> None:
        self.buff.append(data)

    def get(self) -> str:
        return "".join(self.buff)


class ProcessTester(unittest.TestCase):
    def test_capture_stdout(self):
        # out_stream = StringIO()
        with StringIO() as out_stream:
            p = CapturingProcess("echo hi", stdout=out_stream)
            p.wait()
            self.assertIn("hi", out_stream.getvalue())
            self.assertIn("hi", p.get_stdout())

    def test_capture_stderr(self):
        fs = FakeStream()
        cmd = "echo hi >&2"
        p = CapturingProcess(cmd, stderr=fs)
        p.wait()
        self.assertIn("hi", fs.get())
        self.assertIn("hi", p.get_stderr())

    def test_check_wait(self):
        cmd = "garbage_cmd_wont_work"
        p = CapturingProcess(cmd, stdout=FakeStream(), stderr=FakeStream())
        try:
            p.check_wait()
            self.assertTrue(False)
        except subprocess.CalledProcessError:
            self.assertTrue(True)

    def test_main_thread_stream(self):
        """Tests that the stream is always written from the calling thread."""
        tname = threading.current_thread().name
        this = self

        class ThreadStreamChecker:
            def write(self, data: str) -> None:
                this.assertEqual(threading.current_thread().name, tname)

        cmd = "echo hi"
        p = CapturingProcess(cmd, stdout=ThreadStreamChecker(), stderr=FakeStream())
        p.check_wait()
        p = CapturingProcess(cmd, stdout=FakeStream(), stderr=ThreadStreamChecker())
        p.check_wait()


if __name__ == "__main__":
    unittest.main()
