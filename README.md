# pcopy

A simple/experimental parallel file copy utility.

## Overview

File transfers on a network file system often benefit from parallelization. Python's `shutil.copytree(..., copy_function=...)` provides a hook that we can leverage to submit a copy task to a work queue, which can be managed by `concurrent.futures.ThreadPoolExecutor`. The implementation has pleasantly few lines:

```python
class MultithreadedCopier(concurrent.futures.ThreadPoolExecutor):
    def copy(self, source, dest):
        self.submit(shutil.copy2, source, dest)

with MultithreadedCopier(max_workers=workers) as copier:
    shutil.copytree(src, dest, copy_function=copier.copy)
```

That's it! In practice, we add a little bit more code for a CLI, exception handling, and to make it behave like `cp -r src dst` for multiple `src` and for when `dst` exists.

This package is designed to be used from the command line. Install it with pip (probably in a venv) and use the `pcopy` command as one would use `cp -r`:

```bash
pip install git+https://github.com/lgarrison/pcopy
pcopy src dst
```

Or, install it as a "tool" with uv or pipx:

```bash
uv tool install git+https://github.com/lgarrison/pcopy
pcopy src dst
```

Some questions to explore in the future:
- This only parallelizes the file copies (by releasing the GIL), not the directory walk or the directory creation. Can we make a fast Python version that parallelizes those parts?
- Would nogil Python help with that version? Would nogil Python help with the current version?
- Can we get decent small-file/many-dir performance out of Python, or should we use a compiled language?
- What if we want to distribute the work over many nodes?
- Would multi-process be better in any sense than multi-threaded?
- A progress meter would be nice, but that would probably require walking the tree twice.
