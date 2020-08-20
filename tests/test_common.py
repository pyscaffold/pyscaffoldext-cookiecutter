# -*- coding: utf-8 -*-
import sys
from pathlib import Path

import pytest
from pyscaffold import file_system as fs
from pyscaffold import shell

from pyscaffoldext.cookiecutter.extension import Cookiecutter

from .helpers import run, run_common_tasks

COOKIECUTTER = "https://github.com/pyscaffold/cookiecutter-pypackage.git"
FLAG = Cookiecutter().flag
PUTUP = shell.get_executable("putup")


def is_venv():
    """Check if the tests are running inside a venv"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


@pytest.fixture(autouse=True)
def cwd(tmpfolder):
    """Guarantee a blank folder as workspace"""
    yield tmpfolder


def test_ensure_inside_test_venv():
    # This is a METATEST
    # Here we ensure `putup` is installed inside tox or
    # a local virtualenv (pytest-runner), so we know we are testing the correct
    # version of pyscaffold and not one the devs installed to use in other
    # projects
    assert PUTUP
    assert ".tox" in PUTUP or is_venv()


@pytest.mark.slow
@pytest.mark.system
def test_namespace_cookiecutter(tmpfolder):
    # Given pyscaffold is installed,
    # when we call putup with --namespace and --cookiecutter
    run(
        f"{PUTUP} myproj --venv --no-config --namespace nested.ns {FLAG} {COOKIECUTTER}"
    )
    # then a very complicated module hierarchy should exist
    assert Path("myproj/src/nested/ns/myproj").is_dir()
    # and all the common tasks should run properly
    with fs.chdir("myproj"):
        run_common_tasks(tests=False, pre_commit=False)
