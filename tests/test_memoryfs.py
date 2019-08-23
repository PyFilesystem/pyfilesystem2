from __future__ import unicode_literals

import posixpath
import unittest

import pytest

from fs import memoryfs
from fs.test import FSTestCases
from fs.test import UNICODE_TEXT

try:
    # Only supported on Python 3.4+
    import tracemalloc
except ImportError:
    tracemalloc = None


class TestMemoryFS(FSTestCases, unittest.TestCase):
    """Test OSFS implementation."""

    def make_fs(self):
        return memoryfs.MemoryFS()

    def _create_many_files(self):
        for parent_dir in {"/", "/one", "/one/two", "/one/other-two/three"}:
            self.fs.makedirs(parent_dir, recreate=True)
            for file_id in range(50):
                self.fs.writetext(
                    posixpath.join(parent_dir, str(file_id)), UNICODE_TEXT
                )

    @pytest.mark.skipif(
        not tracemalloc, reason="`tracemalloc` isn't supported on this Python version."
    )
    def test_close_mem_free(self):
        """Ensure all file memory is freed when calling close().

        Prevents regression against issue #308.
        """
        trace_filters = [tracemalloc.Filter(True, "*/memoryfs.py")]
        tracemalloc.start()

        before = tracemalloc.take_snapshot().filter_traces(trace_filters)
        self._create_many_files()
        after_create = tracemalloc.take_snapshot().filter_traces(trace_filters)

        self.fs.close()
        after_close = tracemalloc.take_snapshot().filter_traces(trace_filters)
        tracemalloc.stop()

        [diff_create] = after_create.compare_to(
            before, key_type="filename", cumulative=True
        )
        self.assertGreater(
            diff_create.size_diff,
            0,
            "Memory usage didn't increase after creating files; diff is %0.2f KiB."
            % (diff_create.size_diff / 1024.0),
        )

        [diff_close] = after_close.compare_to(
            after_create, key_type="filename", cumulative=True
        )
        self.assertLess(
            diff_close.size_diff,
            0,
            "Memory usage increased after closing the file system; diff is %0.2f KiB."
            % (diff_close.size_diff / 1024.0),
        )
