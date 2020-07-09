# -*- coding: utf-8 -*-
import shlex
import sys
import traceback
from os import environ
from subprocess import STDOUT, CalledProcessError, check_output
from uuid import uuid4


def uniqstr():
    """Generates a unique random long string every time it is called"""
    return str(uuid4()).replace("-", "")


def run(*args, **kwargs):
    # normalize args
    if len(args) == 1:
        if isinstance(args[0], str):
            args = shlex.split(args[0])
        else:
            args = args[0]

    if args[0] == "python" and sys.platform != "win32":
        args[0] += str(sys.version_info[0])

    opts = dict(stderr=STDOUT, universal_newlines=True)
    opts.update(kwargs)

    try:
        output = check_output(args, **opts)
        print("command: ", args, opts)
        print("output: ", output)
        return output
    except CalledProcessError as ex:
        traceback.print_exc()
        msg = "******************** Terminal ($? = {}) ********************\n{}"
        print(msg.format(ex.returncode, ex.output))
        raise


def run_common_tasks(tests=True, flake8=True):
    if tests:
        run("python setup.py test")

    run("python setup.py doctest")
    run("python setup.py docs")
    run("python setup.py --version")
    run("python setup.py sdist")
    run("python setup.py bdist")

    if flake8 and environ.get("COVERAGE") == "true":
        run("flake8 --count")
