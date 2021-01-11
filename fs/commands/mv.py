from fs.path import relpath, normpath, abspath
import os,sys,time
import posixpath

import click
from fs import errors
from ._tools import FS2_NOEXIST, FS2_ISFILE, FS2_ISDIR

def _mv(fs, src, dst, force, vcount=0):
    """move file and dirs.
    example:
        mkdir dir1 dir2
        mkdir -p dir1/sub/dir dir2/
    """
    try:
        fs.move(src, dst, overwrite=force)
    except errors.DestinationExists:
        if not force:
            click.confirm('%s is exist. Overwirte?' % dst, abort=True, default=True)
        fs.move(src, dst, overwrite=True)
    if vcount >= 1:
        print(time.strftime('%F_%T'), 'move %s -> %s' % (src, dst))

@click.command()
@click.argument('src', nargs=-1)
@click.argument('dst', nargs=1)
@click.option('--force', '-f', is_flag=True, help='force overwrite if existing destination file')
@click.option('--verbose', '-v', count=True, help='more info')
@click.pass_context
def mv(ctx, src, dst, force, verbose):
    """move file (same fs).
    ./fs2 mv tox.ini .
    ./fs2 mv tox.ini tmp.ini
    ./fs2 mv tox.ini a.ini dir/ path/to/
    """
    fs = ctx.obj['fs']

    ### check dst part
    dst_is, dirlist = FS2_ISDIR, []
    try:
        dirlist = fs.listdir(dst)
        # if not force:
        #     click.confirm('%s is an exist dir. Continue?' % dst, abort=True, default=True)
    except errors.DirectoryExpected:
        dst_is = FS2_ISFILE
        if not len(src) == 1 or not os.path.isfile(src[0]):
            click.echo('%s is a file so only one file is need' % dst)
            return
        if not force:
            click.confirm('%s is an exist file. Continue?' % dst, abort=True, default=True)
    except errors.ResourceNotFound:
        if len(src) == 1:
            dst_is = FS2_NOEXIST

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
                    fs.makedirs(_dst, recreate=force)
                except errors.DirectoryExists:
                    if not force:
                        click.confirm('%s is an exist dir. Continue?' % _dst, abort=True, default=True)
                for finfo in files:
                    _mv(fs, posixpath.join(top, finfo.name), posixpath.join(_dst, finfo.name), force, verbose)
        except errors.DirectoryExpected:
            _dst = dst
            if dst_is == FS2_ISDIR:
                _dst = posixpath.join(dst, posixpath.basename(fn))
            _mv(fs, fn, _dst, force, verbose)
        except errors.ResourceNotFound:
            if not force:
                click.confirm('%s is not exist. Continue?' % fn, abort=True, default=True)

