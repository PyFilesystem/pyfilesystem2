from __future__ import print_function, unicode_literals

import unittest
from datetime import datetime

from fs.time import datetime_to_epoch, epoch_to_datetime

try:
    from datetime import timezone
except ImportError:
    from fs._tzcompat import timezone  # type: ignore


class TestEpoch(unittest.TestCase):
    def test_epoch_to_datetime(self):
        self.assertEqual(
            epoch_to_datetime(142214400), datetime(1974, 7, 5, tzinfo=timezone.utc)
        )

    def test_datetime_to_epoch(self):
        self.assertEqual(
            datetime_to_epoch(datetime(1974, 7, 5, tzinfo=timezone.utc)), 142214400
        )
