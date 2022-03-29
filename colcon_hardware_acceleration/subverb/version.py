# Copyright 2022 Víctor Mayoral-Vilches
# Licensed under the Apache License, Version 2.0

import os

from colcon_core.plugin_system import satisfies_version
from colcon_hardware_acceleration.subverb import AccelerationSubverbExtensionPoint, get_vitis_dir
from colcon_hardware_acceleration import __version__


class VersionSubverb(AccelerationSubverbExtensionPoint):
    """Report version of the tool."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102
        argument = parser.add_argument(
            "component",
            nargs="?",
            help='Component name (e.g. "vitis" key).',
        )
        # try:
        #     from argcomplete.completers import ChoicesCompleter
        # except ImportError:
        #     pass
        # else:
        #     component_options = ["vitis"]
        #     argument.completer = ChoicesCompleter(component_options)

    def main(self, *, context):  # noqa: D102
        """Version of Vitis being used.

        NOTE: Location, syntax and other related matters are defined
            within the `acceleration_firmware_kv260` package. Refer to it for more
            details.
        """
        if not context.args.component:  # defaults to this package's version
            print(__version__)

        elif context.args.component == "vitis":
            vitis_dir = get_vitis_dir()
