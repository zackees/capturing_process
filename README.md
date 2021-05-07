# Finally, a subprocess type that streams out stdout/stderr easily

Capturing the stderr AND stdout from a process in python is not that easy.
This class makes this capturing much easier by delegating the line capturing
to seperate threads. This capture can be totally in memory or can optionally
be streamed to a output stream such as a file handle.

# Python version: 3.6+

Because of the use of type annotations, this library is not compatible with python 2.7
However you are free to strip out these type annotations and this project *should* work
pretty well.

## TODO
  * Make writing supplied streams something that happens only on the main thread.