"""Place for fixtures and configuration that will be used in most of the tests.
A nice option is to put your ``autouse`` fixtures here.
Functions that can be imported and re-used are more suitable for the ``helpers`` file.
"""
import logging
import os
from pathlib import Path
from tempfile import mkdtemp
from textwrap import dedent

import pytest
from pyscaffold.log import ReportFormatter

from .helpers import rmpath, uniqstr


@pytest.fixture
def tmpfolder(tmp_path):
    old_path = os.getcwd()
    new_path = mkdtemp(dir=str(tmp_path))
    os.chdir(new_path)
    try:
        yield Path(new_path)
    finally:
        os.chdir(old_path)
        rmpath(new_path)


@pytest.fixture(autouse=True)
def cookiecutter_config(tmpfolder, monkeypatch):
    # Define custom "cache" directories for cookiecutter inside a temporary
    # directory per test.
    # This way, if the tests are running in parallel, each test has its own
    # "cache" and stores/removes cookiecutter templates in an isolated way
    # avoiding inconsistencies/race conditions.
    cookiecutters_dir = (tmpfolder / "custom-cookiecutters").resolve()
    cookiecutters_dir.mkdir(exist_ok=True, parents=True)
    replay_dir = (tmpfolder / "cookiecutters-replay").resolve()
    replay_dir.mkdir(exist_ok=True, parents=True)

    (tmpfolder / "cookiecutters-replay").mkdir(exist_ok=True, parents=True)
    config = f"""\
    ---
    cookiecutters_dir: "{cookiecutters_dir}"
    replay_dir: "{replay_dir}"
    """

    config_file = tmpfolder / "cookiecutter.yaml"
    config_file.write_text(dedent(config))
    monkeypatch.setenv("COOKIECUTTER_CONFIG", str(config_file))

    yield config_file


@pytest.fixture
def isolated_log(request, monkeypatch, caplog):
    """See isolated_logger in pyscaffold/tests/conftest.py to see why this fixture
    is important to guarantee tests checking logs work as expected.
    This just work for multiprocess environments, not multithread.
    """
    if "original_logger" in request.keywords:
        yield caplog
        return

    # Get a fresh new logger, not used anywhere
    raw_logger = logging.getLogger(uniqstr())
    raw_logger.setLevel(logging.NOTSET)
    new_handler = logging.StreamHandler()

    patches = {
        "propagate": True,  # <- needed for caplog
        "nesting": 0,
        "wrapped": raw_logger,
        "handler": new_handler,
        "formatter": ReportFormatter(),
    }
    for key, value in patches.items():
        monkeypatch.setattr(f"pyscaffold.log.logger.{key}", value)

    try:
        yield caplog
    finally:
        new_handler.close()
