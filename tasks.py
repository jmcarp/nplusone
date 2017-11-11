# -*- coding: utf-8 -*-

import os
import sys
import webbrowser

from invoke import task


docs_dir = 'docs'
build_dir = os.path.join(docs_dir, '_build')


@task
def test(ctx):
    import pytest
    errcode = pytest.main(['tests'])
    sys.exit(errcode)


@task
def watch(ctx):
    """Run tests when a file changes. Requires pytest-xdist."""
    import pytest
    errcode = pytest.main(['-f'])
    sys.exit(errcode)


@task
def clean(ctx):
    ctx.run('rm -rf build')
    ctx.run('rm -rf dist')
    ctx.run('rm -rf nplusone.egg-info')
    clean_docs(ctx)
    print('Cleaned up.')


@task
def clean_docs(ctx):
    ctx.run('rm -rf {0}'.format(build_dir))


@task
def browse_docs(ctx):
    path = os.path.join(build_dir, 'index.html')
    webbrowser.open_new_tab(path)


@task
def docs(ctx, clean=False, browse=False, watch=False):
    """Build the docs."""
    if clean:
        clean_docs(ctx)
    ctx.run('sphinx-build {0} {1}'.format(docs_dir, build_dir), pty=True)
    if browse:
        browse_docs(ctx)
    if watch:
        watch_docs(ctx)


@task
def watch_docs(ctx):
    """Run build the docs when a file changes."""
    try:
        import sphinx_autobuild  # noqa
    except ImportError:
        print('ERROR: watch task requires the sphinx_autobuild package.')
        print('Install it with:')
        print('    pip install sphinx-autobuild')
        sys.exit(1)
    docs(ctx)
    ctx.run('sphinx-autobuild {} {}'.format(docs_dir, build_dir), pty=True)


@task
def readme(ctx, browse=False):
    ctx.run('rst2html.py README.rst > README.html', pty=True)
    if browse:
        webbrowser.open_new_tab('README.html')
