"""
  This process solves the short comings of subprocess.Popen which is
  stdout/stderr capture WHILE the process is streaming to stdout/stderr.
  This is fixed with this module by writing to a temporary file for
  both stdout/stderr and then streaming that text to stdout/stderr
  while also allowing this to be captured to a log file or emit if a
  fatal error interrupts the build process.

  Tested on win32 and macOS and some flavors of linux.
"""

# pylint: disable=import-error,wrong-import-position

import os
import subprocess
import sys
import time
from typing import Any, Optional

if sys.platform == "win32":
    from colorama import just_fix_windows_console  # type: ignore
    import threading

from capturing_process.stream_thread import StreamThread

if sys.platform == "win32":
    mutex = threading.Lock()


class CapturingProcess:
    """
    Similar to subprocess.Popen() but with the get_stdout(),
    get_stderr(), raise_on_error(). The stderr and stdout streams
    default to sys versions.
    """

    def __init__(
        self,
        cmd: str,
        cwd: Optional[str] = None,
        stdout: Any = None,
        stderr: Any = None,
    ):
        if sys.platform == "win32":
            with mutex:
                just_fix_windows_console()
        self.cmd = cmd
        self.rtn_code: Optional[int] = None
        if cwd is None:
            self.cwd = os.getcwd()
        stdout = stdout or sys.stdout
        stderr = stderr or sys.stderr
        self.proc = subprocess.Popen(  # pylint: disable=R1732
            cmd,
            shell=True,
            cwd=cwd,
            bufsize=0,
            universal_newlines=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.stdout_thread = StreamThread(self.proc.stdout, stdout)
        self.stderr_thread = StreamThread(self.proc.stderr, stderr)

    def wait(self, timeout: Optional[int] = None) -> Optional[int]:
        """Like subprocess.Popen.wait. Plays nice with KeyboardInterrupt."""
        start_time = time.time()
        while self.rtn_code is None:
            self.poll()  # self.rtn_code can be set here.
            if self.rtn_code is not None:
                break
            if timeout is None:
                continue
            if time.time() - start_time > timeout:
                break
            time.sleep(0.1)  # Most friendly to the keyboard interrupt
            # on win32.
        return self.rtn_code

    def check_wait(self) -> None:
        """
        Like wait() but raises a CalledProcessError if the return
        code is not 0.
        """
        self.wait()
        self.raise_on_error()

    def poll(self) -> Optional[int]:
        """Like subprocess.Popen.poll()."""
        if self.rtn_code is None:
            self.rtn_code = self.proc.poll()
            if self.rtn_code is not None:
                self.stdout_thread.join_once()
                self.stderr_thread.join_once()
            self.stdout_thread.pump()
            self.stderr_thread.pump()
        return self.rtn_code

    def kill(self) -> None:
        """Like subprocess.Popen.kill()"""
        self.proc.kill()
        self.stdout_thread.join_once()
        self.stderr_thread.join_once()

    def raise_on_error(self) -> None:
        """
        Checks the return code and if it is a error type
        then CalledProcessError is raised.
        """
        if self.rtn_code is None:
            return
        if self.rtn_code != 0:
            raise subprocess.CalledProcessError(
                self.rtn_code,
                cmd=self.cmd,
                output=self.get_stdout(),
                stderr=self.get_stderr(),
            )

    def get_stdout(self) -> str:
        """Returns all the stdout as one string."""
        return self.stdout_thread.to_string()

    def get_stderr(self) -> str:
        """Returns all the stderr as one string."""
        return self.stderr_thread.to_string()
