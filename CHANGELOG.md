# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## Unrelease

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


