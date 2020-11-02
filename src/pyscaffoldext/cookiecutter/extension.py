"""Extension that integrates cookiecutter templates into PyScaffold.

When used via PyScaffold's Python API (instead of CLI), a ``cookiecutter_params``
keyword argument can be optionally added to :obj:`pyscaffold.api.create_project`,
this argument should be a :obj:`dict` (or a similar object that can be converted to dict
via the :obj:`dict` constructor), and is equivalent to ``extra_context`` in
:obj:`cookicookiecutter.main.cookiecutter` (PyScaffold will always add some default
values, even when no ``cookiecutter_params`` are given).
"""

# This file was transfered from the main PyScaffold repository using
# ``git filter-branch``, and therefore might have lost parts of its
# commit history.
# Please refer to ``pyscaffold`` if that is needed.

from typing import Any, Dict, List

from pyscaffold import file_system as fs
from pyscaffold.actions import Action, ActionParams, ScaffoldOpts, Structure
from pyscaffold.extensions import Extension, store_with
from pyscaffold.log import logger

UPDATE_WARNING = (
    "Updating code generated using external tools is not "
    "supported. The extension `cookiecutter` will be ignored, only "
    "changes in PyScaffold core features will take place."
)


class Cookiecutter(Extension):
    """Additionally apply a Cookiecutter template.
    Note that not all templates are suitable for PyScaffold.
    Please refer to the docs for more information.
    """

    persist = False

    def augment_cli(self, parser):
        """Add an option to parser that enables the Cookiecutter extension
        See :obj:`pyscaffold.extension.Extension.augment_cli`.
        """
        parser.add_argument(
            self.flag,
            dest=self.name,
            action=store_with(self),
            metavar="TEMPLATE",
            help=self.help_text,
        )
        parser.add_argument(
            "--cookiecutter-params",
            nargs="+",
            required=False,
            type=lambda kv: kv.split("=", 1),
            help="extra parameters to be passed to cookiecutter in the form of "
            "a space separated list of 'NAME=VALUE' (check the `cookiecutter.json` "
            "file of the template you are using to see the available parameters). "
            "Please notice PyScaffold already add some default parameters, check the "
            "docs for more information.",
        )

    def activate(self, actions: List[Action]) -> List[Action]:
        """Register before_create hooks to generate project using Cookiecutter
        Activate extension. See :obj:`pyscaffold.extension.Extension.activate`."""
        actions = self.register(actions, enforce_options, before="get_default_options")
        return self.register(actions, create_cookiecutter)


def enforce_options(struct: Structure, opts: ScaffoldOpts) -> ActionParams:
    """Make sure options reflect the cookiecutter usage.
    See :obj:`pyscaffold.actions.Action`.
    """
    opts["force"] = True
    return struct, opts


def parameters(opts: ScaffoldOpts) -> Dict[str, Any]:
    """Parameters to be passed to cookiecutter as ``extra_context``"""
    project_name = opts["project_path"].resolve().name
    return {
        "full_name": opts["author"],
        "author": opts["author"],
        "email": opts["email"],
        "installable_name": opts["name"],
        "package_name": opts["package"],
        "namespace": opts.get("namespace"),
        "repo_name": project_name,
        "project_name": project_name,
        "project_short_description": opts["description"],
        "release_date": opts["release_date"],
        "version": "unknown",  # will be replaced later
        "year": opts["year"],
        **dict(opts.get("cookiecutter_params") or {}),
    }


def create_cookiecutter(struct: Structure, opts: ScaffoldOpts) -> ActionParams:
    """Create a cookie cutter template
    See :obj:`pyscaffold.actions.Action`.
    """
    if opts.get("update"):
        logger.warning(UPDATE_WARNING)
        return struct, opts

    try:
        from cookiecutter.main import cookiecutter
    except Exception as e:
        raise NotInstalled from e

    template = opts.get("cookiecutter")
    if not template:
        raise MissingTemplate

    logger.report("run", "cookiecutter " + opts["cookiecutter"])
    if not opts.get("pretend"):

        with fs.chdir(opts["project_path"].resolve().parent):
            cookiecutter(template, no_input=True, extra_context=parameters(opts))

    return struct, opts


class NotInstalled(RuntimeError):
    """This extension depends on the ``cookiecutter`` package."""

    DEFAULT_MESSAGE = "cookiecutter is not installed, " "run: pip install cookiecutter"

    def __init__(self, message=DEFAULT_MESSAGE, *args, **kwargs):
        super(NotInstalled, self).__init__(message, *args, **kwargs)


class MissingTemplate(RuntimeError):
    """A cookiecutter template (git url) is required."""

    DEFAULT_MESSAGE = "missing `cookiecutter` option"

    def __init__(self, message=DEFAULT_MESSAGE, *args, **kwargs):
        super(MissingTemplate, self).__init__(message, *args, **kwargs)
