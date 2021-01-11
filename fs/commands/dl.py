from fs.path import relpath, normpath, abspath
import os,sys,time
import posixpath
import io

import click
from fs import errors
from ._tools import FS2_NOEXIST, FS2_ISFILE, FS2_ISDIR


def _download(fs, src, dst, vcount=0):
    with open(dst, 'wb') as f:
        fs.download(src, f)
        if vcount >= 1:
            print(time.strftime('%F_%T'), 'transfer %8.3f Kbytes for %s' % (f.tell()/1024, dst))

@click.command()
@click.argument('src', nargs=-1)
@click.argument('dst', nargs=1)
@click.option('--force', '-f', is_flag=True, help='force overwrite if existing destination file')
@click.option('--verbose', '-v', count=True, help='more info')
@click.pass_context
def dl(ctx, src, dst, force, verbose):
    """download file to local disk.

    \b
    example:
        dl a.txt .
        dl a.txt loc/b.txt
        dl ./ locdir/
        dl a.txt b.png c.mp3 dir/d/ remote/dir/
    """
    fs = ctx.obj['fs']

    ### check dst part
    dst_is, dirlist = FS2_ISDIR, []
    try:
        dirlist = os.listdir(dst)
        if not force:
            click.confirm('%s is an exist dir. Continue?' % dst, abort=True, default=True)
    except NotADirectoryError:
        dst_is = FS2_ISFILE
        if not force:
            click.confirm('%s is an exist file. Continue?' % dst, abort=True, default=True)
    except FileNotFoundError:
        if len(src) == 1:
            dst_is = FS2_NOEXIST
        else:
            os.makedirs(dst, exist_ok=True)
            dst_is = FS2_ISDIR

    ### check src part
    for fn in src:
        fn = abspath(fn)
        _dname, _fname = posixpath.split(fn)
        try:
            for top, subs, files in fs.walk.walk(fn):
                # dl remote/dir pathnoexist =>  remote/dir/a/b default to pathnoexist/dir/a/b
                _dst = posixpath.join(dst, top[len(_dname):].lstrip('/'))
                if dst_is == FS2_NOEXIST:
                    _dst = posixpath.join(dst, top[len(fn):].lstrip('/'))    # fix to pathnoexist/a/b
                try:
                    os.makedirs(_dst, exist_ok=force)
                except FileExistsError:
                    if not force:
                        click.confirm('%s is an exist dir. Continue?' % _dst, abort=True, default=True)
                for finfo in files:
                    _download(fs, posixpath.join(top, finfo.name), posixpath.join(_dst, finfo.name), verbose)
        except errors.DirectoryExpected:
            _dst = dst
            if dst_is == FS2_ISDIR:
                _dst = posixpath.join(dst, posixpath.basename(fn))
            _download(fs, fn, _dst, verbose)
        except errors.ResourceNotFound:
            if not force:
                click.confirm('%s is not exist. Continue?' % fn, abort=True, default=True)

