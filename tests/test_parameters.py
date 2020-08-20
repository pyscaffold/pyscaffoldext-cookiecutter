from pathlib import Path

import pytest
from pyscaffold import cli

from pyscaffoldext.cookiecutter.extension import parameters

COOKIECUTTER_URL = "https://github.com/pyscaffold/cookiecutter-pypackage.git"


def test_parse():
    args = [
        "my_proj",
        "--cookiecutter",
        "some-template",
        "--cookiecutter-params",
        "a=1",
        "b=2",
        "c=3",
        "some=param",
    ]
    opts = cli.parse_args(args)
    params = dict(opts["cookiecutter_params"])
    assert params == {"a": "1", "b": "2", "c": "3", "some": "param"}


def test_parameters(tmpfolder):
    opts = {
        "project_path": tmpfolder,
        "author": "John Doe",
        "email": "john.doe@example.com",
        "name": "my-pkg",
        "package": "pkg",
        "namespace": "my",
        "release_date": "today",
        "year": "1906",
        "description": "AWESOME",
    }

    # Given cookiecutter_params that are dicts or can be used to call ``dict``
    for params in ({"extra": 42}, [("extra", 42)], zip(["extra"], [42])):
        # then its contents should be in the result dict
        assert parameters({**opts, "cookiecutter_params": params})["extra"] == 42


@pytest.mark.system
def test_generate_with_params(tmpfolder):
    args = [
        "my_proj",
        "--no-config",  # <- ignore PyScaffold's config files in the dev's machine
        "--cookiecutter",
        COOKIECUTTER_URL,
        "--cookiecutter-params",
        "command_line_interface=Argparse",
        "use_pytest=y",
    ]
    cli.main(args)
    generated_cli = Path("my_proj/src/my_proj/cli.py").read_text()
    assert "argparse" in generated_cli
    assert "click" not in generated_cli
    generated_test = Path("my_proj/tests/test_my_proj.py").read_text()
    assert "pytest" in generated_test
    assert "unittest" not in generated_test
