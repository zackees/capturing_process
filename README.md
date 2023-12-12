# Finally, a subprocess type that streams out stdout/stderr easily

[![Win_Tests](https://github.com/zackees/capturing_process/actions/workflows/push_win.yml/badge.svg)](https://github.com/zackees/capturing_process/actions/workflows/push_win.yml)
[![Ubuntu_Tests](https://github.com/zackees/capturing_process/actions/workflows/push_ubuntu.yml/badge.svg)](https://github.com/zackees/capturing_process/actions/workflows/push_ubuntu.yml)
[![MacOS_Tests](https://github.com/zackees/capturing_process/actions/workflows/push_macos.yml/badge.svg)](https://github.com/zackees/capturing_process/actions/workflows/push_macos.yml)

Capturing the stderr AND stdout from a process in python is not that easy.
This class makes this capturing much easier by delegating the line capturing
to seperate threads. This capture can be totally in memory or can optionally
be streamed to a output stream such as a file handle.

This class will unconditionally launch a shell command and the input will always
be string, not an array like what is accepted by subprocess.Popen().

# Example:

Super simple example:

```python
from capturing_process import CapturingProcess

out_stream = StringIO()
p = CapturingProcess("echo hi", stdout=out_stream)
p.wait()
self.assertIn("hi", out_stream.getvalue())
self.assertIn("hi", p.get_stdout())
```

For splitting the output to stdout and a file you'd write a stream class like so:

```python
class MyStream:
    def __init__(self, filehandle) -> None:
        self.fh = filehandle

    def write(self, data: str) -> None:
        self.fh.write(data)
        sys.stdout.write(data)

with open('myfile', 'w') as fd:
    out_stream = MyStream(fd)
    proc = CapturingProcess("echo hi", stdout=out_stream)
    proc.wait()  # Output will go to file and sys.stdout
```


To silence an output stream (stdout/stderr) drop a StringIO object as an argument to
the CapturingProcess like so:

```python
proc = CapturingProcess("echo hi", stdout=StringIO())
proc.wait()  # stdout redirected to StringIO()
```

## If you want the entire stdout/stderr bytes

```python
proc.get_stdout()
proc.get_stderr()
```

# Python version: 3.6+

Because of the use of type annotations, this library is not compatible with python 2.7
However you are free to strip out these type annotations and this project *should* work
pretty well.

# Links:

   * https://pypi.org/project/capturing-process/
   * https://github.com/zackees/capturing_process


# Versions

  * 1.0.9: stdout/stderr threads are now forcefully killed within .1 second if they don't join.
  * 1.0.8: Fixes CapturingProcess.kill blocking if the stdout and stderr threads fail to join.