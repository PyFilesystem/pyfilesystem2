from fs import open_fs, errors
import shutil
import click

def _listopener():
    from fs.opener  import registry
    openers = set(registry.get_opener(i).__class__ for i in  registry.protocols)
    for opener in openers:
        print(str(opener), 'for', ['%s://' % i for i in opener.protocols])

@click.group(invoke_without_command=True) #https://click.palletsprojects.com/en/7.x/commands/#group-invocation-without-command
@click.option('--listopener', '-l', is_flag=True, help='list supported file system')
@click.option('--url', '-u', default='.', help='filesystem url: default is "."')
@click.pass_context
def fs2(ctx, listopener, url):
    '''This script is pyfilesystem2 command line tool

    \b
    example:
        ./fs2 ls .
        ./fs2 -u file://c:/windows ls system32
        ./fs2 -u zip:///tmp/a.zip ls /
        ./fs2 -u tar:///etc/bak.tar.gz  ls opkg config
        ./fs2 -u temp:// ls .
        ./fs2 -u s3:// ls .                                 # pip install fs-s3fs
        ./fs2 -u dropbox:// ls .                            # pip install fs.dropboxfs
        ./fs2 -u webdav://user:pass@127.0.0.1/web/dav/ ls . # pip install fs.webdavfs
        ./fs2 -u ssh:// ls .                                # pip install fs.sshfs
        ./fs2 --listopener                                  # list all support filesystem
    '''
    # print(vars(ctx), listopener, url)
    if listopener:
        _listopener()
        return
    if not (ctx.args or ctx.invoked_subcommand):
        click.echo(ctx.get_help())
    if '://' not in url:
        url = 'file://' + url
    ctx.ensure_object(dict)
    ctx.obj['url'] = url
    ctx.obj['fs'] = open_fs(url)

