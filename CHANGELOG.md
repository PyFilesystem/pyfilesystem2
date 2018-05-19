# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [2.0.23] - 2018-05-02

- Fix for Markdown on PyPi, no code chang

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

- New `copy_if_newer' functionality in `copy` module.

### Fixed

- Improved `FTPFS` support for non-strict servers.

## [2.0.2] - 2017-03-12

### Changed
- Improved FTP support for non-compliant servers
- Fix for ZipFS implied directories

## [2.0.1] - 2017-03-11

### Added
- TarFS contributed by Martin Larralde

### Fixed

- FTPFS bugs.

## [2.0.0] - 2016-12-07

New version of the PyFilesystem API.


