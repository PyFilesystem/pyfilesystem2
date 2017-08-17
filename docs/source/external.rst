External Filesystems
====================

The following filesystems work with the FS interface, but are not built-in the the fs module. Please see the documentation for how to install them.

SSH |ci ssh|
------------
`fs.sshfs <https://pypi.python.org/pypi/fs.sshfs/>`_ implements a Pyfilesystem2 filesystem running over the `SSH <https://en.wikipedia.org/wiki/Secure_Shell>`_ protocol, using `paramiko <https://pypi.python.org/pypi/paramiko>`_.

.. |ci ssh| image:: https://img.shields.io/travis/althonos/fs.sshfs/master.svg
   :target: https://travis-ci.org/althonos/fs.sshfs/branches

SMB |ci smb|
------------
`fs.smbfs <https://pypi.python.org/pypi/fs.smbfs/>`_ implements a Pyfilesystem2 filesystem running over the `SMB <https://en.wikipedia.org/wiki/Server_Message_Block>`_ protocol, using `pysmb <https://pypi.python.org/pypi/pysmb>`_.

.. |ci smb| image:: https://img.shields.io/travis/althonos/fs.smbfs/master.svg
   :target: https://travis-ci.org/althonos/fs.smbfs/branches


WebDAV |ci webdav|
------------------
`fs.webdavfs <https://pypi.python.org/pypi/fs.webdavfs/>`_ implements Pyfilesystem2 over the `WebDAV <https://en.wikipedia.org/wiki/WebDAV>`_ protocol.

.. |ci webdav| image:: https://img.shields.io/travis/PyFilesystem/webdavfs/master.svg
   :target: https://travis-ci.org/PyFilesystem/webdavfs/branches
