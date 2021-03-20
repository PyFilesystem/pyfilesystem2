"""

Implements a thread pool for parallel copying of files.

"""

from __future__ import unicode_literals

import threading
import typing

from six.moves.queue import Queue

from .copy import copy_file_internal
from .errors import BulkCopyFailed

if typing.TYPE_CHECKING:
    from .base import FS
    from types import TracebackType
    from typing import List, Optional, Text, Type


class _Worker(threading.Thread):
    """Worker thread that pulls tasks from a queue."""

    def __init__(self, copier):
        # type (Copier) -> None
        self.copier = copier
        super(_Worker, self).__init__()
        self.daemon = True

    def run(self):
        # type () -> None
        queue = self.copier.queue
        while True:
            task = queue.get(block=True)
            try:
                if task is None:
                    break  # Sentinel to exit thread
                task()
            except Exception as error:
                self.copier.add_error(error)
            finally:
                queue.task_done()


class _Task(object):
    """Base class for a task."""

    def __call__(self):
        # type: () -> None
        """Task implementation."""


class _CopyTask(_Task):
    """A callable that copies from one file another."""

    def __init__(
        self,
        src_fs,  # type: FS
        src_path,  # type: Text
        dst_fs,  # type: FS
        dst_path,  # type: Text
        preserve_time,  # type: bool
    ):
        # type: (...) -> None
        self.src_fs = src_fs
        self.src_path = src_path
        self.dst_fs = dst_fs
        self.dst_path = dst_path
        self.preserve_time = preserve_time

    def __call__(self):
        # type: () -> None
        copy_file_internal(
            self.src_fs,
            self.src_path,
            self.dst_fs,
            self.dst_path,
            preserve_time=self.preserve_time,
        )


class Copier(object):
    """Copy files in worker threads."""

    def __init__(self, num_workers=4):
        # type: (int) -> None
        if num_workers < 0:
            raise ValueError("num_workers must be >= 0")
        self.num_workers = num_workers
        self.queue = None  # type: Optional[Queue[_Task]]
        self.workers = []  # type: List[_Worker]
        self.errors = []  # type: List[Exception]
        self.running = False

    def start(self):
        """Start the workers."""
        if self.num_workers:
            self.queue = Queue()
            self.workers = [_Worker(self) for _ in range(self.num_workers)]
            for worker in self.workers:
                worker.start()
        self.running = True

    def stop(self):
        """Stop the workers (will block until they are finished)."""
        if self.running and self.num_workers:
            for _worker in self.workers:
                self.queue.put(None)
            for worker in self.workers:
                worker.join()
            # Free up references held by workers
            del self.workers[:]
            self.queue.join()
        self.running = False

    def add_error(self, error):
        """Add an exception raised by a task."""
        self.errors.append(error)

    def __enter__(self):
        self.start()
        return self

    def __exit__(
        self,
        exc_type,  # type: Optional[Type[BaseException]]
        exc_value,  # type: Optional[BaseException]
        traceback,  # type: Optional[TracebackType]
    ):
        self.stop()
        if traceback is None and self.errors:
            raise BulkCopyFailed(self.errors)

    def copy(self, src_fs, src_path, dst_fs, dst_path, preserve_time=False):
        # type: (FS, Text, FS, Text, bool) -> None
        """Copy a file from one fs to another."""
        if self.queue is None:
            # This should be the most performant for a single-thread
            copy_file_internal(
                src_fs, src_path, dst_fs, dst_path, preserve_time=preserve_time
            )
        else:
            task = _CopyTask(src_fs, src_path, dst_fs, dst_path, preserve_time)
            self.queue.put(task)
