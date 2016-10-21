
from __future__ import unicode_literals

import datetime
import unittest

import pytz

from fs.enums import ResourceType
from fs.info import Info
from fs.permissions import Permissions
from fs.time import datetime_to_epoch


class TestInfo(unittest.TestCase):

    def test_empty(self):
        """Test missing info."""
        info = Info({})

        self.assertIsNone(info.name)
        self.assertIsNone(info.is_dir)
        self.assertEqual(info.type, ResourceType.unknown)
        self.assertIsNone(info.accessed)
        self.assertIsNone(info.modified)
        self.assertIsNone(info.created)
        self.assertIsNone(info.metadata_changed)
        self.assertIsNone(info.accessed)
        self.assertIsNone(info.permissions)
        self.assertIsNone(info.user)
        self.assertIsNone(info.group)

    def test_access(self):
        info = Info({
            "access": {
                "uid": 10,
                "gid": 12,
                "user": 'will',
                "group": 'devs',
                "permissions": ['u_r']
            }
        })
        self.assertIsInstance(info.permissions, Permissions)
        self.assertEqual(info.permissions, Permissions(user='r'))
        self.assertEqual(info.user, 'will')
        self.assertEqual(info.group, 'devs')
        self.assertEqual(info.uid, 10)
        self.assertEqual(info.gid, 12)

    def test_basic(self):
        # Check simple file
        info = Info({
            "basic": {
                "name": "bar",
                "is_dir": False
            }
        })
        self.assertEqual(info.name, "bar")
        self.assertIsInstance(info.is_dir, bool)
        self.assertFalse(info.is_dir)
        self.assertEqual(repr(info), "<file 'bar'>")

        # Check dir
        info = Info({
            "basic": {
                "name": "foo",
                "is_dir": True
            }
        })
        self.assertTrue(info.is_dir)
        self.assertEqual(repr(info), "<dir 'foo'>")

    def test_details(self):
        dates = [
            datetime.datetime(2016, 7, 5, tzinfo=pytz.UTC),
            datetime.datetime(2016, 7, 6, tzinfo=pytz.UTC),
            datetime.datetime(2016, 7, 7, tzinfo=pytz.UTC),
            datetime.datetime(2016, 7, 8, tzinfo=pytz.UTC)
        ]
        epochs = [datetime_to_epoch(d) for d in dates]

        info = Info({
            "details": {
                "accessed": epochs[0],
                "modified": epochs[1],
                "created": epochs[2],
                "metadata_changed": epochs[3],
                "type": int(ResourceType.file)
            }
        })
        self.assertEqual(info.accessed, dates[0])
        self.assertEqual(info.modified, dates[1])
        self.assertEqual(info.created, dates[2])
        self.assertEqual(info.metadata_changed, dates[3])
        self.assertIsInstance(info.type, ResourceType)
        self.assertEqual(info.type, ResourceType.file)
        self.assertEqual(info.type, 2)

    def test_has_namespace(self):
        info = Info({
            "basic": {},
            "details": {}
        })
        self.assertTrue(info.has_namespace('basic'))
        self.assertTrue(info.has_namespace('details'))
        self.assertFalse(info.has_namespace('access'))

    def test_copy(self):
        info = Info({
            "basic": {
                "name": "bar",
                "is_dir": False
            }
        })
        info_copy = info.copy()
        self.assertEqual(info.raw, info_copy.raw)

