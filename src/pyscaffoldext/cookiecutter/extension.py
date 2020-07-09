# -*- coding: utf-8 -*-
"""
Extension that integrates cookiecutter templates into PyScaffold.
"""

# This file was transfered from the main PyScaffold repository using
# ``git filter-branch``, and therefore might have lost parts of its
# commit history.
# Please refer to ``pyscaffold`` if that is needed.

import argparse

from pyscaffold.api import Extension
from pyscaffold.api.helpers import logger, register
from pyscaffold.warnings import UpdateNotSupported


class Cookiecutter(Extension):
    """Additionally apply a Cookiecutter template"""

    mutually_exclusive = True

    try:
        # TODO: Remove this try/except block on PyScaffold >= 4.x
        from pyscaffold.extensions import cookiecutter  # Check if builtin existis

        del cookiecutter

        # WORKAROUND:
        #
        # This avoids raising an error by using `add_argument` with an
        # option/flag that was already used and at the same time provides
        # a unequivocal way of accessing the newest implementation in the
        # tests via the `--x-` prefix.
        #
        # For the time being this is useful to run against an existing
        # version of PyScaffold that have an old implementation of this
        # extension built into the core of the system.

        @property
        def xhelp(self):
            return ("Newest version of `{}`, in development".format(self.flag),)

        @property
        def xflag(self):
            return "--x-" + self.flag.strip("-")

    except ImportError:
        pass  # Never mind, we are in a recent version of PyScaffold

    def augment_cli(self, parser):
        """Add an option to parser that enables the Cookiecutter extension

        Args:
            parser (argparse.ArgumentParser): CLI parser object
        """
        # TODO: Simplify the x stuff for PyScaffold >= 4.x
        flag = getattr(self, "xflag", self.flag)
        help = getattr(
            self,
            "xhelp",
            "additionally apply a Cookiecutter template. "
            "Note that not all templates are suitable for PyScaffold. "
            "Please refer to the docs for more information.",
        )

        parser.add_argument(
            flag,
            dest=self.name,
            action=create_cookiecutter_parser(self),
            metavar="TEMPLATE",
            help=help,
        )

    def activate(self, actions):
        """Register before_create hooks to generate project using Cookiecutter

        Args:
            actions (list): list of actions to perform

        Returns:
            list: updated list of actions
        """
        # `get_default_options` uses passed options to compute derived ones,
        # so it is better to prepend actions that modify options.
        actions = register(
            actions, enforce_cookiecutter_options, before="get_default_options"
        )

        # `apply_update_rules` uses CWD information,
        # so it is better to prepend actions that modify it.
        actions = register(actions, create_cookiecutter, before="apply_update_rules")

        return actions


def create_cookiecutter_parser(obj_ref):
    """Create a Cookiecutter parser.

    Args:
        obj_ref (Extension): object reference to the actual extension

    Returns:
        NamespaceParser: parser for namespace cli argument
    """

    class CookiecutterParser(argparse.Action):
        """Consumes the values provided, but also append the extension function
        to the extensions list.
        """

        def __call__(self, parser, namespace, values, option_string=None):
            # First ensure the extension function is stored inside the
            # 'extensions' attribute:
            extensions = getattr(namespace, "extensions", [])
            extensions.append(obj_ref)
            namespace.extensions = extensions

            # Now the extra parameters can be stored
            setattr(namespace, self.dest, values)

            # save the cookiecutter cli argument for later
            obj_ref.args = values

    return CookiecutterParser


def enforce_cookiecutter_options(struct, opts):
    """Make sure options reflect the cookiecutter usage.

    Args:
        struct (dict): project representation as (possibly) nested
            :obj:`dict`.
        opts (dict): given options, see :obj:`create_project` for
            an extensive list.

    Returns:
        struct, opts: updated project representation and options
    """
    opts["force"] = True

    return struct, opts


def create_cookiecutter(struct, opts):
    """Create a cookie cutter template

    Args:
        struct (dict): project representation as (possibly) nested
            :obj:`dict`.
        opts (dict): given options, see :obj:`create_project` for
            an extensive list.

    Returns:
        struct, opts: updated project representation and options
    """
    if opts.get("update"):
        logger.warning(UpdateNotSupported(extension="cookiecutter"))
        return struct, opts

    try:
        from cookiecutter.main import cookiecutter
    except Exception as e:
        raise NotInstalled from e

    extra_context = dict(
        full_name=opts["author"],
        author=opts["author"],
        email=opts["email"],
        project_name=opts["project"],
        package_name=opts["package"],
        repo_name=opts["package"],
        project_short_description=opts["description"],
        release_date=opts["release_date"],
        version="unknown",  # will be replaced later
        year=opts["year"],
    )

    if "cookiecutter" not in opts:
        raise MissingTemplate

    logger.report("run", "cookiecutter " + opts["cookiecutter"])
    if not opts.get("pretend"):
        cookiecutter(opts["cookiecutter"], no_input=True, extra_context=extra_context)

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
