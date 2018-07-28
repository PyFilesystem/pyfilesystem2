from __future__ import unicode_literals

import unittest

from fs._bulk import Copier, _Task
from fs.errors import BulkCopyFailed


class BrokenTask(_Task):
    def __call__(self):
        1 / 0


class TestBulk(unittest.TestCase):
    def test_worker_error(self):
        with self.assertRaises(BulkCopyFailed):
            with Copier(num_workers=2) as copier:
                copier.queue.put(BrokenTask())
