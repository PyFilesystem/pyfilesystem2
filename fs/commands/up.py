from fs.path import relpath, normpath, abspath
import os,sys,time
import posixpath
import io

import click
from fs import errors
from ._tools import FS2_NOEXIST, FS2_ISFILE, FS2_ISDIR

def _upload(fs, src, dst, vcount=0):
    with open(src, 'rb') as f:
        fs.upload(dst, f)
        if vcount >= 1:
            print(time.strftime('%F_%T'), 'transfer %8.3f Kbytes for %s' % (f.tell()/1024, dst))

@click.command()
@click.argument('src', nargs=-1)
@click.argument('dst', nargs=1)
@click.option('--force', '-f', is_flag=True, help='force overwrite if existing destination file')
@click.option('--verbose', '-v', count=True, help='more info')
@click.pass_context
def up(ctx, src, dst, force, verbose):
    """upload local disk file to remote filesystem.

    \b
    example:
        up a.txt .
        up a.txt b.txt
        up a.txt b.png c.mp3 dir/d/ remote/dir/
        up ./ remote/
    """
    fs = ctx.obj['fs']

    ### check dst part
    dst_is, dirlist = FS2_ISDIR, []
    try:
        dirlist = fs.listdir(dst)
        if not force:
            click.confirm('%s is an exist dir. Continue?' % dst, abort=True, default=True)
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
        if not os.path.exists(fn):
            click.echo("%s must be an exist" % fn)
            return
        _dname, _fname = posixpath.split(fn)
        if os.path.isfile(fn):
            _dst = dst
            if dst_is == FS2_ISDIR:
                _dst = posixpath.join(dst,posixpath.basename(fn))
            _upload(fs, fn, _dst, verbose)
        else:
            for top, subs, files in os.walk(fn):
                # up loc/dir pathnoexist =>  loc/dir/a/b default to pathnoexist/dir/a/b
                _dst = posixpath.join(dst, top[len(_dname):].lstrip('/'))
                if dst_is == FS2_NOEXIST and len(src) == 1:
                    _dst = posixpath.join(dst, top[len(fn):].lstrip('/'))    # fix to pathnoexist/a/b
                try:
                    fs.makedirs(_dst, recreate=force)
                except errors.DirectoryExists:
                    click.confirm('%s is an exist dir. Continue?' % _dst, abort=True, default=True)
                for locname in files:
                    _upload(fs, posixpath.join(top, locname), posixpath.join(_dst, locname), verbose)


