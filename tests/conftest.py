#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for custom_extension.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""
import builtins
import os
import shlex
import stat
from contextlib import contextmanager
from shutil import rmtree

import pytest


def set_writable(func, path, exc_info):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise RuntimeError


@pytest.fixture
def tmpfolder(tmpdir):
    old_path = os.getcwd()
    newpath = str(tmpdir)
    os.chdir(newpath)
    try:
        yield tmpdir
    finally:
        os.chdir(old_path)
        rmtree(newpath, onerror=set_writable)


@pytest.fixture
def venv(virtualenv):
    """Create a virtualenv for each test"""
    return virtualenv


@pytest.fixture
def venv_run(venv):
    """Run a command inside the venv"""

    def _run(*args, **kwargs):
        # pytest-virtualenv doesn't play nicely with external os.chdir
        # so let's be explicit about it...
        kwargs["cd"] = os.getcwd()
        kwargs["capture"] = True
        if len(args) == 1 and isinstance(args[0], str):
            args = shlex.split(args[0])
        return venv.run(args, **kwargs).strip()

    return _run


@contextmanager
def disable_import(prefix):
    """Avoid packages being imported

    Args:
        prefix: string at the beginning of the package name
    """
    realimport = builtins.__import__

    def my_import(name, *args, **kwargs):
        if name.startswith(prefix):
            raise ImportError
        return realimport(name, *args, **kwargs)

    try:
        builtins.__import__ = my_import
        yield
    finally:
        builtins.__import__ = realimport


@pytest.fixture
def nocookiecutter_mock():
    with disable_import("cookiecutter"):
        yield


@pytest.fixture
def cookiecutter_config(tmpfolder):
    # Define custom "cache" directories for cookiecutter inside a temporary
    # directory per test.
    # This way, if the tests are running in parallel, each test has its own
    # "cache" and stores/removes cookiecutter templates in an isolated way
    # avoiding inconsistencies/race conditions.
    config = (
        'cookiecutters_dir: "{dir}/custom-cookiecutters"\n'
        'replay_dir: "{dir}/cookiecutters-replay"'
    ).format(dir=str(tmpfolder))

    tmpfolder.mkdir("custom-cookiecutters")
    tmpfolder.mkdir("cookiecutters-replay")

    config_file = tmpfolder.join("cookiecutter.yaml")
    config_file.write(config)
    os.environ["COOKIECUTTER_CONFIG"] = str(config_file)

    yield

    del os.environ["COOKIECUTTER_CONFIG"]
