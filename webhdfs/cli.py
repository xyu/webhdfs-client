#!/usr/bin/env python
#
# Copyright (c) 2017 luyi@neucloud.cn
#

import click
import json
import os
import time

from webhdfs import WebHDFS


@click.group()
def hdfs_cli():
  with open(os.path.expanduser('~') + '/.whdfsc.json', 'r') as f:
    cfg = json.load(f)
  global hdfs
  hdfs = WebHDFS(**cfg)


@hdfs_cli.command()
def home():
  """ get home dir
  """
  click.echo(hdfs.home)


@hdfs_cli.command()
@click.argument('path', nargs=-1, required=True)
def stat(path):
  """ get files/dirs status
  """
  for p in path:
    # avoid abspath from parsing relative path
    p = os.path.abspath('/' + p)[1:]
    if p != '/':
      p = p.rstrip('/')
    if p.startswith('/'):
      click.echo('{}:'.format(p))
    else:
      click.echo('~/{}:'.format(p))
    try:
      r = hdfs.get_file_status(p)
      click.echo(json.dumps(r, indent=2))
    except Exception as e:
      click.echo(str(e))


@hdfs_cli.command()
@click.argument('path', nargs=-1)
def ls(path):
  """ list files/dirs status
  """
  def get_bits(file_type, permission, acl=False):
    bt = file_type[0].lower().replace('f', '-')
    bp_all = 'rwxrwxrwx'
    bp = ''
    # convert oct string
    pm = int(permission, 8)
    for i in range(8, -1, -1):
      bp += '-' if (pm & 2**i == 0) else bp_all[8-i]
    if (pm & 2**9 != 0):
      # sticky bit
      bp = bp[:-1] + ('t' if bp[-1] == 'x' else 'T')
    ba = '+' if acl else ' '
    return bt + bp + ba

  if not path:
    path = ['']
  for p in path:
    # avoid abspath from parsing relative path
    p = os.path.abspath('/' + p)[1:]
    if p != '/':
      p = p.rstrip('/')
    if p.startswith('/'):
      click.echo('{}:'.format(p))
    else:
      click.echo('~/{}:'.format(p))
    try:
      res = hdfs.list_status(p)
      if not res:
        print '(empty)'
        continue
      fmt = '{{}} {{:{}}} {{:{}}} {{:>{}}} {{}} {{}}'.format(
        max([len(r['owner']) for r in res]),
        max([len(r['group']) for r in res]),
        max([len(str(r['length'])) for r in res])
      )
      for r in res:
        b = get_bits(r['type'], r['permission'], r.get('aclBit', False))
        t = time.strftime(
          '%F %H:%M',
          time.localtime(r['modificationTime']/1000)
        )
        if not r['pathSuffix'] or p in ('/', ''):
          f = p + r['pathSuffix']
        else:
          f = p + '/' + r['pathSuffix']
        click.echo(
          fmt.format(b, r['owner'], r['group'], r['length'], t, f)
        )
    except Exception as e:
      click.echo(str(e))


@hdfs_cli.command()
@click.argument('files', nargs=-1, required=True)
def cat(files):
  """ output file content
  """
  for f in files:
    try:
      click.echo(hdfs.open(f))
    except Exception as e:
      click.echo(str(e))


@hdfs_cli.command()
@click.argument('src', nargs=-1, required=True)
@click.argument('dst', nargs=1)
def mv(src, dst):
  """ move(rename) files/dirs
  """
  for s in src:
    ddst = '{}/{}'.format(dst.rstrip('/'), os.path.basename(s))
    if not hdfs.rename(s, ddst) and not hdfs.rename(s, dst):
      click.echo('cannot move {} to {}'.format(s, dst))


@hdfs_cli.command()
@click.option('-p', '--permission', default='700')
@click.option('-f', '--force', is_flag=True)
@click.argument('src', nargs=1)
@click.argument('dst', nargs=1)
def put(src, dst, permission, force):
  """ copy from local
  """
  if not os.path.isfile(src):
    click.echo('no such file: {}'.format(src))
  try:
    hdfs.put(dst, src, permission, force)
  except Exception as e:
    click.echo(str(e))


@hdfs_cli.command()
@click.option('-f', '--force', is_flag=True)
@click.argument('src', nargs=1)
@click.argument('dst', nargs=1)
def get(src, dst, force):
  """ copy to local
  """
  if os.path.isfile(dst) and not force:
    click.echo('file already exists: {}'.format(dst))
  try:
    hdfs.get(src, dst)
  except Exception as e:
    click.echo(str(e))


@hdfs_cli.command()
@click.option('-p', '--permission', default='700')
@click.argument('dirs', nargs=-1, required=True)
def mkdir(dirs, permission):
  """ make dirs
  """
  for d in dirs:
    if not hdfs.mkdirs(d, permission):
      click.echo('cannot make dir {}'.format(a))


@hdfs_cli.command()
@click.option('-r', '--recursive', is_flag=True)
@click.argument('path', nargs=-1, required=True)
def rm(path, recursive):
  """ delete files/dirs
  """
  for p in path:
    if not hdfs.delete(p, recursive):
      click.echo('cannot delete {}'.format(a))


@hdfs_cli.command()
@click.option('-o', '--owner', default='')
@click.option('-g', '--group', default='')
@click.argument('path', nargs=-1, required=True)
def chown(path, owner, group):
  """ set owner of files/dirs
  """
  for p in path:
    try:
      hdfs.setowner(p, owner, group)
    except Exception as e:
      click.echo(str(e))


@hdfs_cli.command()
@click.option('-p', '--permission', default='700')
@click.argument('path', nargs=-1, required=True)
def chmod(path, permission):
  """ set permission of files/dirs
  """
  for p in path:
    try:
      hdfs.set_permission(p, permission)
    except Exception as e:
      click.echo(str(e))


@hdfs_cli.command()
@click.argument('path', nargs=-1)
def summary(path):
  """ get content summary of a dir
  """
  if not path:
    path = ['']
  for p in path:
    # avoid abspath from parsing relative path
    p = os.path.abspath('/' + p)[1:]
    if p != '/':
      p = p.rstrip('/')
    if p.startswith('/'):
      click.echo('{}:'.format(p))
    else:
      click.echo('~/{}:'.format(p))
    try:
      r = hdfs.get_content_summary(p)
      click.echo(json.dumps(r, indent=2))
    except Exception as e:
      click.echo(str(e))


if __name__ == "__main__":
  hdfs_cli()
