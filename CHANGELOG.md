# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## Unreleased


## [2.4.16] - 2022-05-02

### Changed

- Make `fs.zipfs._ZipExtFile` use the seeking mechanism implemented
  in the Python standard library in Python version 3.7 and later
  ([#527](https://github.com/PyFilesystem/pyfilesystem2/pull/527)).
- Mark `fs.zipfs.ReadZipFS` as a case-sensitive filesystem
  ([#527](https://github.com/PyFilesystem/pyfilesystem2/pull/527)). 
- Optimized moving files between filesystems with syspaths.
  ([#523](https://github.com/PyFilesystem/pyfilesystem2/pull/523)).
- Fixed `fs.move.move_file` to clean up the copy on the destination in case of errors.
- `fs.opener.manage_fs` with `writeable=True` will now raise a `ResourceReadOnly`
  exception if the managed filesystem is not writeable.
- Marked filesystems wrapped with `fs.wrap.WrapReadOnly` as read-only.


## [2.4.15] - 2022-02-07

### Changed

- Support more lenient usernames and group names in FTP servers
  ([#507](https://github.com/PyFilesystem/pyfilesystem2/pull/507)).
  Closes [#506](https://github.com/PyFilesystem/pyfilesystem2/issues/506).
- Removed dependency on pytz ([#518](https://github.com/PyFilesystem/pyfilesystem2/pull/518)).
  Closes [#516](https://github.com/PyFilesystem/pyfilesystem2/issues/518).

### Fixed

- Fixed `MemoryFS.move` and `MemoryFS.movedir` not updating the name of moved
  resources, causing `MemoryFS.scandir` to use the old name.
  ([#510](https://github.com/PyFilesystem/pyfilesystem2/pull/510)).
  Closes [#509](https://github.com/PyFilesystem/pyfilesystem2/issues/509).
- Make `WrapFS.move` and `WrapFS.movedir` use the delegate FS methods instead
  of `fs.move` functions, which was causing optimized implementation of 
  `movedir` to be always skipped.
  ([#511](https://github.com/PyFilesystem/pyfilesystem2/pull/511)).


## [2.4.14] - 2021-11-16

### Added

- Added `fs.copy.copy_file_if`, `fs.copy.copy_dir_if`, and `fs.copy.copy_fs_if`.
  Closes [#458](https://github.com/PyFilesystem/pyfilesystem2/issues/458).
- Added `fs.base.FS.getmodified`.

### Changed

- FTP servers that do not support the MLST command now try to use the MDTM command to
  retrieve the last modification timestamp of a resource.
  Closes [#456](https://github.com/PyFilesystem/pyfilesystem2/pull/456).

### Fixed

- Fixed performance bugs in `fs.copy.copy_dir_if_newer`. Test cases were adapted to catch those bugs in the future.
- Fixed precision bug for timestamps in `fs.OSFS.setinfo`.


## [2.4.13] - 2021-03-27

### Added

- Added FTP over TLS (FTPS) support to FTPFS.
  Closes [#437](https://github.com/PyFilesystem/pyfilesystem2/issues/437),
  [#449](https://github.com/PyFilesystem/pyfilesystem2/pull/449).
- `PathError` now supports wrapping an exception using the `exc` argument.
  Closes [#453](https://github.com/PyFilesystem/pyfilesystem2/issues/453).
- Better documentation of the `writable` parameter of `fs.open_fs`, and
  hint about using `fs.wrap.read_only` when a read-only filesystem is
  required. Closes [#441](https://github.com/PyFilesystem/pyfilesystem2/issues/441).
- Copy and move operations now provide a parameter `preserve_time` that, when
  passed as `True`, makes sure the "mtime" of the destination file will be
  the same as that of the source file.

### Changed

- Make `FS.upload` explicit about the expected error when the parent directory of the destination does not exist.
  Closes [#445](https://github.com/PyFilesystem/pyfilesystem2/pull/445).
- Migrate continuous integration from Travis-CI to GitHub Actions and introduce several linters
  again in the build steps ([#448](https://github.com/PyFilesystem/pyfilesystem2/pull/448)).
  Closes [#446](https://github.com/PyFilesystem/pyfilesystem2/issues/446).
- Stop requiring `pytest` to run tests, allowing any test runner supporting `unittest`-style
  test suites.
- `FSTestCases` now builds the large data required for `upload` and `download` tests only
  once in order to reduce the total testing time.
- `MemoryFS.move` and `MemoryFS.movedir` will now avoid copying data.
  Closes [#452](https://github.com/PyFilesystem/pyfilesystem2/issues/452).
- `FS.removetree("/")` behaviour has been standardized in all filesystems, and
  is expected to clear the contents of the root folder without deleting it.
  Closes [#471](https://github.com/PyFilesystem/pyfilesystem2/issues/471).
- `FS.getbasic` is now deprecated, as it is redundant with `FS.getinfo`,
  and `FS.getinfo` is now explicitly expected to return the *basic* info
  namespace unconditionally. Closes [#469](https://github.com/PyFilesystem/pyfilesystem2/issues/469).

### Fixed

- Make `FTPFile`, `MemoryFile` and `RawWrapper` accept [`array.array`](https://docs.python.org/3/library/array.html)
  arguments for the `write` and `writelines` methods, as expected by their base class [`io.RawIOBase`](https://docs.python.org/3/library/io.html#io.RawIOBase).
- Various documentation issues, including `MemoryFS` docstring not rendering properly.
- Avoid creating a new connection on every call of `FTPFS.upload`. Closes [#455](https://github.com/PyFilesystem/pyfilesystem2/issues/455).
- `WrapReadOnly.removetree` not raising a `ResourceReadOnly` when called. Closes [#468](https://github.com/PyFilesystem/pyfilesystem2/issues/468).
- `WrapCachedDir.isdir` and `WrapCachedDir.isfile` raising a `ResourceNotFound` error on non-existing path ([#470](https://github.com/PyFilesystem/pyfilesystem2/pull/470)).
- `FTPFS` not listing certain entries with sticky/SUID/SGID permissions set by Linux server ([#473](https://github.com/PyFilesystem/pyfilesystem2/pull/473)).
  Closes [#451](https://github.com/PyFilesystem/pyfilesystem2/issues/451).
- `scandir` iterator not being closed explicitly in `OSFS.scandir`, occasionally causing a `ResourceWarning`
  to be thrown. Closes [#311](https://github.com/PyFilesystem/pyfilesystem2/issues/311).
- Incomplete type annotations for the `temp_fs` parameter of `WriteTarFS` and `WriteZipFS`.
  Closes [#410](https://github.com/PyFilesystem/pyfilesystem2/issues/410).


## [2.4.12] - 2021-01-14

### Added

- Missing `mode` attribute to `_MemoryFile` objects returned by `MemoryFS.openbin`.
- Missing `readinto` method for `MemoryFS` and `FTPFS` file objects. Closes
  [#380](https://github.com/PyFilesystem/pyfilesystem2/issues/380).
- Added compatibility if a Windows FTP server returns file information to the
  `LIST` command with 24-hour times. Closes [#438](https://github.com/PyFilesystem/pyfilesystem2/issues/438).
- Added Python 3.9 support. Closes [#443](https://github.com/PyFilesystem/pyfilesystem2/issues/443).

### Changed

- Start testing on PyPy. Due to [#342](https://github.com/PyFilesystem/pyfilesystem2/issues/342)
  we have to treat PyPy builds specially and allow them to fail, but at least we'll
  be able to see if we break something aside from known issues with FTP tests.
- Include docs in source distributions as well as the whole tests folder,
  ensuring `conftest.py` is present, fixes [#364](https://github.com/PyFilesystem/pyfilesystem2/issues/364).
- Stop patching copy with Python 3.8+ because it already uses `sendfile`
  ([#424](https://github.com/PyFilesystem/pyfilesystem2/pull/424)).
  Closes [#421](https://github.com/PyFilesystem/pyfilesystem2/issues/421).

### Fixed

- Fixed crash when CPython's -OO flag is used
- Fixed error when parsing timestamps from a FTP directory served from a WindowsNT FTP Server.
  Closes [#395](https://github.com/PyFilesystem/pyfilesystem2/issues/395).
- Fixed documentation of `Mode.to_platform_bin`. Closes [#382](https://github.com/PyFilesystem/pyfilesystem2/issues/382).
- Fixed the code example in the "Testing Filesystems" section of the
  "Implementing Filesystems" guide. Closes [#407](https://github.com/PyFilesystem/pyfilesystem2/issues/407).
- Fixed `FTPFS.openbin` not implicitly opening files in binary mode like expected
  from `openbin`. Closes [#406](https://github.com/PyFilesystem/pyfilesystem2/issues/406).


## [2.4.11] - 2019-09-07

### Added

- Added geturl for TarFS and ZipFS for 'fs' purpose. NoURL for 'download' purpose.
- Added helpful root path in CreateFailed exception.
  Closes [#340](https://github.com/PyFilesystem/pyfilesystem2/issues/340).
- Added Python 3.8 support.

### Fixed

- Fixed tests leaving tmp files
- Fixed typing issues
- Fixed link namespace returning bytes
- Fixed broken FSURL in windows [#329](https://github.com/PyFilesystem/pyfilesystem2/issues/329)
- Fixed hidden exception at fs.close() when opening an absent zip/tar file URL [#333](https://github.com/PyFilesystem/pyfilesystem2/issues/333)
- Fixed abstract class import from `collections` which would break on Python 3.8
- Fixed incorrect imports of `mock` on Python 3
- Removed some unused imports and unused `requirements.txt` file
- Added mypy checks to Travis. Closes [#332](https://github.com/PyFilesystem/pyfilesystem2/issues/332).
- Fixed missing `errno.ENOTSUP` on PyPy. Closes [#338](https://github.com/PyFilesystem/pyfilesystem2/issues/338).
- Fixed bug in a decorator that would trigger an `AttributeError` when a class
  was created that implemented a deprecated method and had no docstring of its
  own.

### Changed

- Entire test suite has been migrated to [pytest](https://docs.pytest.org/en/latest/). Closes [#327](https://github.com/PyFilesystem/pyfilesystem2/issues/327).
- Style checking is now enforced using `flake8`; this involved some code cleanup
  such as removing unused imports.

## [2.4.10] - 2019-07-29

### Fixed

- Fixed broken WrapFS.movedir [#322](https://github.com/PyFilesystem/pyfilesystem2/issues/322).

## [2.4.9] - 2019-07-28

### Fixed

- Restored fs.path import
- Fixed potential race condition in makedirs. Fixes [#310](https://github.com/PyFilesystem/pyfilesystem2/issues/310)
- Added missing methods to WrapFS. Fixed [#294](https://github.com/PyFilesystem/pyfilesystem2/issues/294)

### Changed

- `MemFS` now immediately releases all memory it holds when `close()` is called,
  rather than when it gets garbage collected. Closes [issue #308](https://github.com/PyFilesystem/pyfilesystem2/issues/308).
- `FTPFS` now translates `EOFError` into `RemoteConnectionError`. Closes [#292](https://github.com/PyFilesystem/pyfilesystem2/issues/292)
- Added automatic close for filesystems that go out of scope. Fixes [#298](https://github.com/PyFilesystem/pyfilesystem2/issues/298)

## [2.4.8] - 2019-06-12

### Changed

- `geturl` will return URL with user/password if needed @zmej-serow

## [2.4.7] - 2019-06-08

### Added

- Flag to OSFS to disable env var expansion

## [2.4.6] - 2019-06-08

### Added

- Implemented `geturl` in FTPFS @zmej-serow

### Fixed

- Fixed FTP test suite when time is not UTC-0 @mrg0029
- Fixed issues with paths in tarfs https://github.com/PyFilesystem/pyfilesystem2/issues/284

### Changed

- Dropped Python3.3 support

## [2.4.5] - 2019-05-05

### Fixed

- Restored deprecated `setfile` method with deprecation warning to change to `writefile`
- Fixed exception when a tarfile contains a path called '.' https://github.com/PyFilesystem/pyfilesystem2/issues/275
- Made TarFS directory loading lazy

### Changed

- Detect case insensitivity using by writing temp file

## [2.4.4] - 2019-02-23

### Fixed

- OSFS fail in nfs mounts

## [2.4.3] - 2019-02-23

### Fixed

- Fixed broken "case_insensitive" check
- Fixed Windows test fails

## [2.4.2] - 2019-02-22

### Fixed

- Fixed exception when Python runs with -OO

## [2.4.1] - 2019-02-20

### Fixed

- Fixed hash method missing from WrapFS

## [2.4.0] - 2019-02-15

### Added

- Added `exclude` and `filter_dirs` arguments to walk
- Micro-optimizations to walk

## [2.3.1] - 2019-02-10

### Fixed

- Add encoding check in OSFS.validatepath

## [2.3.0] - 2019-01-30

### Fixed

- IllegalBackReference had mangled error message

### Added

- FS.hash method

## [2.2.1] - 2019-01-06

### Fixed

- `Registry.install` returns its argument.

## [2.2.0] - 2019-01-01

A few methods have been renamed for greater clarity (but functionality remains the same).

The old methods are now aliases and will continue to work, but will
issue a deprecation warning via the `warnings` module.
Please update your code accordingly.

- `getbytes` -> `readbytes`
- `getfile` -> `download`
- `gettext` -> `readtext`
- `setbytes` -> `writebytes`
- `setbinfile` -> `upload`
- `settext` -> `writetext`

### Changed

- Changed default chunk size in `copy_file_data` to 1MB
- Added `chunk_size` and `options` to `FS.upload`

## [2.1.3] - 2018-12-24

### Fixed

- Incomplete FTPFile.write when using `workers` @geoffjukes
- Fixed AppFS not creating directory

### Added

- Added load_extern switch to opener, fixes #228 @althanos

## [2.1.2] - 2018-11-10

### Added

- Support for Windows NT FTP servers @sspross

### Fixed

- Root dir of MemoryFS accesible as a file
- Packaging issues @televi
- Deprecation warning re collections.Mapping

## [2.1.1] - 2018-10-03

### Added

- Added PEP 561 py.typed files
- Use sendfile for faster copies @althonos
- Atomic exclusive mode in Py2.7 @sqwishy

### Fixed

- Fixed lstat @kamomil

## [2.1.0] - 2018-08-12

### Added

- fs.glob support

## [2.0.27] - 2018-08-05

### Fixed

- Fixed for Winows paths #152
- Fixed ftp dir parsing (@dhirschfeld)

## [2.0.26] - 2018-07-26

### Fixed

- fs.copy and fs.move disable workers if not thread-safe
- fs.match detects case insensitivity
- Open in exclusive mode is atomic (@squishy)
- Exceptions can be pickleabe (@Spacerat)

## [2.0.25] - 2018-07-20

### Added

- workers parameter to fs.copy, fs.move, and fs.mirror for concurrent
  copies

## [2.0.24] - 2018-06-28

### Added

- timeout to FTP opener

## [2.0.23] - 2018-05-02

- Fix for Markdown on PyPi, no code changes

## [2.0.22] - 2018-05-02

### Fixed

- Handling of broken unicode on Python2.7

### Added

- Added fs.getospath

## [2.0.21] - 2018-05-02

### Added

- Typing information
- Added Info.suffix, Info.suffixes, Info.stem attributes

### Fixed

- Fixed issue with implied directories in TarFS

### Changed

- Changed path.splitext so that 'leading periods on the basename are
  ignored', which is the behaviour of os.path.splitext

## [2.0.20] - 2018-03-13

### Fixed

- MultiFS.listdir now correctly filters out duplicates

## [2.0.19] - 2018-03-11

### Fixed

- encoding issue with TarFS
- CreateFailed now contains the original exception in `exc` attribute

## [2.0.18] - 2018-01-31

### Added

- fs.getfile function

### Changed

- Modified walk to use iterators internally (for more efficient walking)
- Modified fs.copy to use getfile

## [2.0.17] - 2017-11-20

### Fixed

- Issue with ZipFS files missing a byte

## [2.0.16] - 2017-11-11

### Added

- fs.parts

### Fixed

- Walk now yields Step named tuples as advertised

### Added

- Added max_depth parameter to fs.walk

## [2.0.15] - 2017-11-05

### Changed

- ZipFS files are now seekable (Martin Larralde)

## [2.0.14] - 2016-11-05

No changes, pushed wrong branch to PyPi.

## [2.0.13] - 2017-10-17

### Fixed

- Fixed ignore_errors in walk.py

## [2.0.12] - 2017-10-15

### Fixed

- settext, appendtext, appendbytes, setbytes now raise a TypeError if
  the type is wrong, rather than ValueError
- More efficient feature detection for FTPFS
- Fixes for `fs.filesize`
- Major documentation refactor (Martin Larralde)

## [2.0.11]

### Added

- fs.mirror

## [2.0.10]

### Added

- Added params support to FS URLs

### Fixed

- Many fixes to FTPFS contributed by Martin Larralde.

## [2.0.9]

### Changed

- MountFS and MultiFS now accept FS URLS
- Add openers for AppFS

## [2.0.8] - 2017-08-13

### Added

- Lstat info namespace
- Link info namespace
- FS.islink method
- Info.is_link method

## [2.0.7] - 2017-08-06

### Fixes

- Fixed entry point breaking pip

## [2.0.6] - 2017-08-05

### Fixes

- Opener refinements

## [2.0.5] - 2017-08-02

### Fixed

- Fixed potential for deadlock in MemoryFS

### Added

- Added factory parameter to opendir.
- ClosingSubFS.
- File objects are all derived from io.IOBase.

### Fixed

- Fix closing for FTP opener.

## [2.0.4] - 2017-06-11

### Added

- Opener extension mechanism contributed by Martin Larralde.
- Support for pathlike objects.

### Fixed

- Stat information was missing from info.

### Changed

- More specific error when `validatepath` throws an error about the path
  argument being the wrong type, and changed from a ValueError to a
  TypeError.
- Deprecated `encoding` parameter in OSFS.

## [2.0.3] - 2017-04-22

### Added

- New `copy_if_newer` functionality in `copy` module.

### Fixed

- Improved `FTPFS` support for non-strict servers.

## [2.0.2] - 2017-03-12

### Changed

- Improved FTP support for non-compliant servers
- Fix for `ZipFS` implied directories

## [2.0.1] - 2017-03-11

### Added

- `TarFS` contributed by Martin Larralde.

### Fixed

- `FTPFS` bugs.

## [2.0.0] - 2016-12-07

New version of the PyFilesystem API.
