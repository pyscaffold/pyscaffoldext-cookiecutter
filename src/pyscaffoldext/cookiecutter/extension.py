"""
Extension that integrates cookiecutter templates into PyScaffold.
"""

# This file was transfered from the main PyScaffold repository using
# ``git filter-branch``, and therefore might have lost parts of its
# commit history.
# Please refer to ``pyscaffold`` if that is needed.

from typing import List

from pyscaffold import file_system as fs
from pyscaffold.actions import Action, ActionParams, ScaffoldOpts, Structure
from pyscaffold.extensions import Extension, store_with
from pyscaffold.log import logger
from pyscaffold.warnings import UpdateNotSupported


class Cookiecutter(Extension):
    """Additionally apply a Cookiecutter template.
    Note that not all templates are suitable for PyScaffold.
    Please refer to the docs for more information.
    """

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


def create_cookiecutter(struct: Structure, opts: ScaffoldOpts) -> ActionParams:
    """Create a cookie cutter template
    See :obj:`pyscaffold.actions.Action`.
    """
    if opts.get("update"):
        logger.warning(UpdateNotSupported(extension="cookiecutter"))
        return struct, opts

    try:
        from cookiecutter.main import cookiecutter
    except Exception as e:
        raise NotInstalled from e

    project_path = opts["project_path"].resolve()
    parent = project_path.parent
    project_name = project_path.name
    extra_context = dict(
        full_name=opts["author"],
        author=opts["author"],
        email=opts["email"],
        installable_name=opts["name"],
        package_name=opts["package"],
        namespace=opts.get("namespace"),
        repo_name=project_name,
        project_name=project_name,
        project_short_description=opts["description"],
        release_date=opts["release_date"],
        version="unknown",  # will be replaced later
        year=opts["year"],
    )

    if "cookiecutter" not in opts:
        raise MissingTemplate

    logger.report("run", "cookiecutter " + opts["cookiecutter"])
    if not opts.get("pretend"):
        with fs.chdir(parent):
            cookiecutter(
                opts["cookiecutter"], no_input=True, extra_context=extra_context
            )

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
