# Finally, a subprocess type that streams out stdout/stderr easily

Capturing the stderr AND stdout from a process in python is not that easy.
This class makes this capturing much easier by delegating the line capturing
to seperate threads. This capture can be totally in memory or can optionally
be streamed to a output stream such as a file handle.

## TODO
  * Make writing supplied streams something that happens only on the main thread.