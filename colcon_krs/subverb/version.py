# Copyright (c) 2021, Xilinx®
# All rights reserved
#
# Author: Víctor Mayoral Vilches <victorma@xilinx.com>
import os

from colcon_core.plugin_system import satisfies_version
from colcon_krs.subverb import KRSSubverbExtensionPoint, get_vitis_dir
from colcon_krs import __version__


class VersionSubverb(KRSSubverbExtensionPoint):
    """Report version of the tool."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(KRSSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102
        argument = parser.add_argument(
            "component",
            nargs="?",
            help='Component name (e.g. "vitis" key).',
        )
        try:
            from argcomplete.completers import ChoicesCompleter
        except ImportError:
            pass
        else:
            component_options = ["vitis"]
            argument.completer = ChoicesCompleter(component_options)

    def main(self, *, context):  # noqa: D102
        """Version of Vitis being used.

        NOTE: Location, syntax and other related matters are defined
            within the `xilinx_firmware` package. Refer to it for more
            details.
        """
        if not context.args.component:  # defaults to this package's version
            print(__version__)

        elif context.args.component == "vitis":
            vitis_dir = get_vitis_dir()
