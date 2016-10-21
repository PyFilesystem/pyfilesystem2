from __future__ import print_function
from __future__ import unicode_literals

import shutil
import tempfile

import six

from . import errors
from .osfs import OSFS


@six.python_2_unicode_compatible
class TempFS(OSFS):

    def __init__(self,
                 identifier=None,
                 temp_dir=None,
                 auto_clean=True,
                 ignore_clean_errors=True):
        self.identifier = identifier
        self._auto_clean = auto_clean
        self._ignore_clean_errors = ignore_clean_errors
        self._cleaned = False

        self.identifier = (identifier or '__tempfs__').replace('/', '-')

        self._temp_dir = tempfile.mkdtemp(
            identifier or "fsTempFS",
            dir=temp_dir
        )
        super(TempFS, self).__init__(self._temp_dir)

    def __repr__(self):
        return "TempFS()"

    def __str__(self):
        return "<tempfs '{}'>".format(self._temp_dir)

    def close(self):
        if self._auto_clean:
            self.clean()
        super(TempFS, self).close()

    def clean(self):
        """Clean (delete) temporary files created by this filesystem."""
        if self._cleaned:
            return

        try:
            shutil.rmtree(self._temp_dir)
        except Exception as e:
            if not self._ignore_clean_errors:
                raise errors.OperationFailed(
                    msg="failed to remove temporary directory",
                    exc=e
                )
        self._cleaned = True
