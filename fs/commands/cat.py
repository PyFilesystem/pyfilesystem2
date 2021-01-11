import sys
import click
from fs import errors
from fs.path import relpath, normpath

@click.command()
@click.argument('paths', nargs=-1)
@click.option('--force', '-f', is_flag=True, help='force skip if instead of aborting')
@click.pass_context
def cat(ctx, paths, force):
    '''read file and print content.

    \b
    example:
        cat a.txt
        cat a.ini a.txt
    '''
    fs = ctx.obj['fs']
    for path in paths:
        path = relpath(normpath(path))
        try:
            result = fs.readbytes(path)
        except errors.FileExpected:
            if not force:
                click.confirm('Error: %s/ is a dir. Skip?' % path, abort=True, default=True)
        except errors.ResourceNotFound:
            if not force:
                click.confirm('Error: %s is not exist. Skip?' % path, abort=True, default=True)
        else:
            click.echo(result.decode(sys.getdefaultencoding(), 'replace'))

