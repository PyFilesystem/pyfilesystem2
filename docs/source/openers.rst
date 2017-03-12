FS URLs
=======

PyFilesystem可以通过FS URL打开文件系统，这类似于您可能输入到浏览器的URL。

如果您希望能够在conf文件中（例如）动态指定文件系统，则使用FS URL可能非常有用。

FS URL将解析为以下格式::

    <type>://<username>:<password>@<resource>


组件如下：

* ``<type>`` 标识要创建的文件系统的类型。 例如 ``osfs`` , ``ftp`` 。
* ``<username>`` 可选用户名。
* ``<password>`` 可选密码。
* ``<resource>`` *resource*，它可以是一个域，路径或两者。

以下是几个示例::

    osfs://~/projects
    osfs://c://system32
    ftp://ftp.example.org/pub
    mem://

如果 ``<类型>`` 没有指定是它被认为是一个 :class:`~fs.osfs.OSFS` 。 以下FS URL等效::

    osfs://~/projects
    ~/projects

要打开与FS URL的filesysem，你可以使用 :meth:`~fs.opener.Registry.open_fs`，它可以被导入和使用方法如下::

    from fs import open_fs
    projects_fs = open_fs('osfs://~/projects')
