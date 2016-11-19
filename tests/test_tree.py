from __future__ import unicode_literals

import io
import unittest

from fs import tree
from fs.memoryfs import MemoryFS


class TestInfo(unittest.TestCase):

    def setUp(self):
        self.fs = MemoryFS()
        self.fs.makedir('foo')
        self.fs.makedir('bar')
        self.fs.makedir('baz')
        self.fs.makedirs('foo/egg1')
        self.fs.makedirs('foo/egg2')
        self.fs.create('/root1')
        self.fs.create('/root2')
        self.fs.create('/foo/test.txt')
        self.fs.create('/foo/test2.txt')
        self.fs.create('/foo/.hidden')
        self.fs.makedirs('/deep/deep1/deep2/deep3/deep4/deep5/deep6')

    def test_tree(self):

        output_file = io.StringIO()

        tree.render(self.fs, file=output_file)

        expected = '|-- bar\n|-- baz\n|-- deep\n|   `-- deep1\n|       `-- deep2\n|           `-- deep3\n|               `-- deep4\n|                   `-- deep5\n|-- foo\n|   |-- egg1\n|   |-- egg2\n|   |-- .hidden\n|   |-- test.txt\n|   `-- test2.txt\n|-- root1\n`-- root2\n'
        self.assertEqual(output_file.getvalue(), expected)

    def test_tree_encoding(self):

        output_file = io.StringIO()

        tree.render(self.fs, file=output_file, with_color=True)

        print(repr(output_file.getvalue()))

        expected = u'\x1b[32m\u251c\u2500\u2500\x1b[0m \x1b[1;34mbar\x1b[0m\n\x1b[32m\u251c\u2500\u2500\x1b[0m \x1b[1;34mbaz\x1b[0m\n\x1b[32m\u251c\u2500\u2500\x1b[0m \x1b[1;34mdeep\x1b[0m\n\x1b[32m\u2502   \u2514\u2500\u2500\x1b[0m \x1b[1;34mdeep1\x1b[0m\n\x1b[32m\u2502       \u2514\u2500\u2500\x1b[0m \x1b[1;34mdeep2\x1b[0m\n\x1b[32m\u2502           \u2514\u2500\u2500\x1b[0m \x1b[1;34mdeep3\x1b[0m\n\x1b[32m\u2502               \u2514\u2500\u2500\x1b[0m \x1b[1;34mdeep4\x1b[0m\n\x1b[32m\u2502                   \u2514\u2500\u2500\x1b[0m \x1b[1;34mdeep5\x1b[0m\n\x1b[32m\u251c\u2500\u2500\x1b[0m \x1b[1;34mfoo\x1b[0m\n\x1b[32m\u2502   \u251c\u2500\u2500\x1b[0m \x1b[1;34megg1\x1b[0m\n\x1b[32m\u2502   \u251c\u2500\u2500\x1b[0m \x1b[1;34megg2\x1b[0m\n\x1b[32m\u2502   \u251c\u2500\u2500\x1b[0m \x1b[33m.hidden\x1b[0m\n\x1b[32m\u2502   \u251c\u2500\u2500\x1b[0m test.txt\n\x1b[32m\u2502   \u2514\u2500\u2500\x1b[0m test2.txt\n\x1b[32m\u251c\u2500\u2500\x1b[0m root1\n\x1b[32m\u2514\u2500\u2500\x1b[0m root2\n'
        self.assertEqual(output_file.getvalue(), expected)

    def test_tree_bytes_no_dirs_first(self):

        output_file = io.StringIO()

        tree.render(self.fs, file=output_file, dirs_first=False)

        expected = u'|-- bar\n|-- baz\n|-- deep\n|   `-- deep1\n|       `-- deep2\n|           `-- deep3\n|               `-- deep4\n|                   `-- deep5\n|-- foo\n|   |-- .hidden\n|   |-- egg1\n|   |-- egg2\n|   |-- test.txt\n|   `-- test2.txt\n|-- root1\n`-- root2\n'
        self.assertEqual(output_file.getvalue(), expected)

    def test_error(self):
        output_file = io.StringIO()

        filterdir = self.fs.filterdir

        def broken_filterdir(path, **kwargs):
            if path.startswith('/deep/deep1/'):
                # Because error messages differ accross Python versions
                raise Exception('integer division or modulo by zero')
            return filterdir(path, **kwargs)
        self.fs.filterdir = broken_filterdir
        tree.render(self.fs, file=output_file, with_color=True)

        expected = u'\x1b[32m\u251c\u2500\u2500\x1b[0m \x1b[1;34mbar\x1b[0m\n\x1b[32m\u251c\u2500\u2500\x1b[0m \x1b[1;34mbaz\x1b[0m\n\x1b[32m\u251c\u2500\u2500\x1b[0m \x1b[1;34mdeep\x1b[0m\n\x1b[32m\u2502   \u2514\u2500\u2500\x1b[0m \x1b[1;34mdeep1\x1b[0m\n\x1b[32m\u2502       \u2514\u2500\u2500\x1b[0m \x1b[1;34mdeep2\x1b[0m\n\x1b[32m\u2502           \u2514\u2500\u2500\x1b[0m \x1b[31merror (integer division or modulo by zero)\x1b[0m\n\x1b[32m\u251c\u2500\u2500\x1b[0m \x1b[1;34mfoo\x1b[0m\n\x1b[32m\u2502   \u251c\u2500\u2500\x1b[0m \x1b[1;34megg1\x1b[0m\n\x1b[32m\u2502   \u251c\u2500\u2500\x1b[0m \x1b[1;34megg2\x1b[0m\n\x1b[32m\u2502   \u251c\u2500\u2500\x1b[0m \x1b[33m.hidden\x1b[0m\n\x1b[32m\u2502   \u251c\u2500\u2500\x1b[0m test.txt\n\x1b[32m\u2502   \u2514\u2500\u2500\x1b[0m test2.txt\n\x1b[32m\u251c\u2500\u2500\x1b[0m root1\n\x1b[32m\u2514\u2500\u2500\x1b[0m root2\n'
        tree_output = output_file.getvalue()
        print(repr(tree_output))

        self.assertEqual(expected, tree_output)

        output_file = io.StringIO()
        tree.render(self.fs, file=output_file, with_color=False)

        expected = u'|-- bar\n|-- baz\n|-- deep\n|   `-- deep1\n|       `-- deep2\n|           `-- error (integer division or modulo by zero)\n|-- foo\n|   |-- egg1\n|   |-- egg2\n|   |-- .hidden\n|   |-- test.txt\n|   `-- test2.txt\n|-- root1\n`-- root2\n'
        self.assertEqual(expected, output_file.getvalue())
