import logging
import os
import re
from configparser import ConfigParser
from pathlib import Path

import pytest
from pyscaffold import __version__ as pyscaffold_version
from pyscaffold.api import NO_CONFIG, create_project
from pyscaffold.cli import parse_args, run
from pyscaffold.templates import get_template

from pyscaffoldext.cookiecutter.extension import (
    Cookiecutter,
    MissingTemplate,
    NotInstalled,
)

from .helpers import disable_import

pytestmark = [pytest.mark.usefixtures("cookiecutter_config")]

PROJ_NAME = "proj"
COOKIECUTTER_URL = "https://github.com/pyscaffold/cookiecutter-pypackage.git"
COOKIECUTTER_FILES = ["proj/Makefile", "proj/.github/ISSUE_TEMPLATE.md"]

FLAG = Cookiecutter().flag


@pytest.mark.slow
def test_create_project_with_cookiecutter(tmpfolder):
    # Given options with the cookiecutter extension,
    opts = dict(
        project_path=PROJ_NAME,
        name=PROJ_NAME,
        package=PROJ_NAME,
        version=pyscaffold_version,
        cookiecutter=COOKIECUTTER_URL,
        extensions=[Cookiecutter()],
        config_files=NO_CONFIG,
    )
    # NO_CONFIG: avoid extra config from dev's machine interference

    # when the project is created,
    create_project(opts)

    # then cookiecutter files should exist
    for file in COOKIECUTTER_FILES:
        assert Path(file).exists()

    # and also overwritable pyscaffold files (with the exact contents)
    setup_py = (tmpfolder / PROJ_NAME / "setup.py").read_text()
    assert get_template("setup_py").safe_substitute(opts) == setup_py

    # and the cookiecutter configuration should NOT be stored in setup.cfg
    # (persist = False, since we do not support updates)
    existing_setup = (tmpfolder / PROJ_NAME / "setup.cfg").read_text()
    cfg = ConfigParser()
    cfg.read_string(existing_setup)
    assert "cookiecutter" not in cfg["pyscaffold"]


def test_pretend_create_project_with_cookiecutter(tmpfolder, isolated_log):
    # Given options with the cookiecutter extension,
    isolated_log.set_level(logging.INFO)
    opts = parse_args([PROJ_NAME, "--no-config", "--pretend", FLAG, COOKIECUTTER_URL])
    # --no-config: avoid extra config from dev's machine interference

    # when the project is created,
    create_project(opts)

    # then files should exist
    assert not Path(PROJ_NAME).exists()
    for file in COOKIECUTTER_FILES:
        assert not Path(file).exists()

    # but activities should be logged
    logs = isolated_log.text
    assert re.search(r"run.+cookiecutter", logs)


def test_create_project_with_cookiecutter_but_no_template(tmpfolder):
    # Given options with the cookiecutter extension, but no template
    opts = dict(
        project_path=PROJ_NAME, extensions=[Cookiecutter()], config_files=NO_CONFIG
    )
    # NO_CONFIG: avoid extra config from dev's machine interference

    # when the project is created,
    # then an exception should be raised.
    with pytest.raises(MissingTemplate):
        create_project(opts)


def test_create_project_without_cookiecutter(tmpfolder):
    # Given options without the cookiecutter extension,
    opts = dict(project_path=PROJ_NAME, config_files=NO_CONFIG)
    # NO_CONFIG: avoid extra config from dev's machine interference

    # when the project is created,
    create_project(opts)

    # then cookiecutter files should not exist
    for file in COOKIECUTTER_FILES:
        assert not Path(file).exists()


@disable_import("cookiecutter")
def test_create_project_no_cookiecutter(tmpfolder):
    # Given options with the cookiecutter extension,
    # but without cookiecutter being installed,
    opts = dict(
        project_path=PROJ_NAME,
        cookiecutter=COOKIECUTTER_URL,
        extensions=[Cookiecutter()],
        config_files=NO_CONFIG,
    )

    # when the project is created,
    # then an exception should be raised.
    with pytest.raises(NotInstalled):
        create_project(opts)


def test_create_project_cookiecutter_and_update(tmpfolder, capfd):
    # Given a project exists
    create_project(project_path=PROJ_NAME, config_files=NO_CONFIG)

    # when the project is updated
    # with the cookiecutter extension,
    opts = dict(
        project_path=PROJ_NAME,
        update=True,
        cookiecutter=COOKIECUTTER_URL,
        extensions=[Cookiecutter()],
    )
    create_project(opts)

    # then a warning should be displayed
    out, err = capfd.readouterr()
    out_err = out + err
    try:
        assert "external tools" in out_err
        assert "not supported" in out_err
        assert "will be ignored" in out_err
    except AssertionError:
        if os.name == "nt":
            pytest.skip("pytest is having problems to capture stderr/stdout on Windows")
        else:
            raise


@pytest.mark.slow
def test_cli_with_cookiecutter(tmpfolder):
    assert not (tmpfolder / PROJ_NAME).exists()

    # Given the command line with the cookiecutter option,
    args = ["--no-config", PROJ_NAME, FLAG, COOKIECUTTER_URL]
    # --no-config: avoid extra config from dev's machine interference

    # when pyscaffold runs,
    run(args)

    # then cookiecutter files should exist
    for file in COOKIECUTTER_FILES:
        assert Path(file).exists()


def test_cli_with_cookiecutter_but_no_template(tmpfolder, capfd):
    # Given the command line with the cookiecutter option, but no template
    args = ["--no-config", PROJ_NAME, FLAG]
    # --no-config: avoid extra config from dev's machine interference

    # when pyscaffold runs,
    # then an exception should be raised.
    with pytest.raises(SystemExit):
        run(args)

    # make sure the exception is related to the missing argument
    out, err = capfd.readouterr()
    assert "{}: expected one argument".format(FLAG) in out + err


def test_cli_without_cookiecutter(tmpfolder):
    # Given the command line without the cookiecutter option,
    args = ["--no-config", PROJ_NAME]
    # --no-config: avoid extra config from dev's machine interference

    # when pyscaffold runs,
    run(args)

    # then cookiecutter files should not exist
    for file in COOKIECUTTER_FILES:
        assert not Path(file).exists()


def test_cli_with_cookiecutter_and_update(tmpfolder, capfd):
    # Given a project exists
    create_project(project_path=PROJ_NAME, config_files=NO_CONFIG)

    # when the project is updated
    # with the cookiecutter extension,
    args = ["--no-config", PROJ_NAME, "--update", FLAG, COOKIECUTTER_URL]
    # --no-config: avoid extra config from dev's machine interference
    run(args)

    # then a warning should be displayed
    out, err = capfd.readouterr()
    out_err = out + err
    try:
        assert "external tools" in out_err
        assert "not supported" in out_err
        assert "will be ignored" in out_err
    except AssertionError:
        if os.name == "nt":
            pytest.skip("pytest is having problems to capture stderr/stdout on Windows")
        else:
            raise
