# -*- coding: utf-8 -*-
import sys
from os.path import isdir

import pytest

from .helpers import run, run_common_tasks

pytestmark = [pytest.mark.slow, pytest.mark.system]

COOKIECUTTER = "https://github.com/pyscaffold/cookiecutter-pypackage.git"


def is_venv():
    """Check if the tests are running inside a venv"""
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


@pytest.fixture(autouse=True)
def cwd(tmpdir):
    """Guarantee a blank folder as workspace"""
    with tmpdir.as_cwd():
        yield tmpdir


def test_ensure_inside_test_venv():
    # This is a METATEST
    # Here we ensure `putup` is installed inside tox or
    # a local virtualenv (pytest-runner), so we know we are testing the correct
    # version of pyscaffold and not one the devs installed to use in other
    # projects
    assert ".tox" in run("which putup") or is_venv()


def test_namespace_cookiecutter(cwd):
    # Given pyscaffold is installed,
    # when we call putup with --namespace and --cookiecutter
    run("putup myproj --namespace nested.ns --cookiecutter " + COOKIECUTTER)
    # then a very complicated module hierarchy should exist
    assert isdir("myproj/src/nested/ns/myproj")
    # and all the common tasks should run properly
    with cwd.join("myproj").as_cwd():
        run_common_tasks(flake8=False, tests=False)
