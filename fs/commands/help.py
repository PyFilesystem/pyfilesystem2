#!/usr/bin/env python
import click
from fs import errors

@click.command()
@click.pass_context
def help(ctx):
    '''print this help msg.'''
    click.echo(ctx.parent.get_help()) # ctx.parent -> fs2 level

