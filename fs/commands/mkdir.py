import click
from fs import errors
from fs.path import relpath, normpath
import posixpath

@click.command()
@click.argument('paths', nargs=-1)
@click.option('--parents', '-p', is_flag=True, help='no error if existing, make parent directories as needed')
@click.option('--force', '-f', is_flag=True, help='force skip if instead of aborting')
@click.pass_context
def mkdir(ctx, paths, parents, force):
    """create folders.
    example:
        mkdir dir1 dir2
        mkdir -p dir1/sub/dir dir2/
    """
    fs = ctx.obj['fs']
    for path in paths:
        try:
            if parents:
                fs.makedirs(path, recreate=True)
            else:
                fs.makedir(path, recreate=True)
        except errors.ResourceNotFound:
            if not force:
                click.confirm('parent dir %s not exist. Skip?' % posixpath.dirname(path), abort=True, default=True)
        except errors.DirectoryExpected as e:
            click.echo('%s. Check Tip: %s' % (e, path.replace('/', '(<-aFile?) / ')))
            break

