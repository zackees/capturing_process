import subprocess
import unittest
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
        fs = FakeStream()
        p = CapturingProcess("echo hi", stdout=fs)
        p.wait()
        self.assertIn("hi", fs.get())
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


if __name__ == "__main__":
    unittest.main()
