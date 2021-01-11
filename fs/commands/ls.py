import click
from fs import errors
from fs.path import relpath, normpath

from ._words2lines import words2lines

@click.command()
@click.argument('paths', nargs=-1, required=False)
@click.option('--force', '-f', is_flag=True, help='force skip instead of aborting')
@click.pass_context
def ls(ctx, paths, force):
    '''list files and dirs.
    example:
        ls .
        ls dirA dirx/ a/b.txt
    '''
    fs = ctx.obj['fs']
    url = ctx.obj['url']
    paths = paths or ['.']
    for path in paths:
        _path = path
        path = relpath(normpath(path))
        try:
            names = fs.listdir(path)
            if url.lower().startswith('file://') or url.lower().startswith('osfs://'):
                names.sort(key=lambda x: x.lstrip('.').lstrip('_').lower()) # sort as /bin/ls do
                # names = ['.', '..'] + names       # need not
            if len(paths) > 1:
                print('%s/:' % _path.rstrip('/'))
            print('\n'.join(words2lines(names)))
        except errors.DirectoryExpected:
            print('%s:' % _path.rstrip('/'))
        except errors.ResourceNotFound:
            if not force:
                click.confirm('%s is not exist. Skip?' % _path, abort=True, default=True)
        print()
