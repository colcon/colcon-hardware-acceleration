# Copyright (c) 2021, Xilinx®
# All rights reserved
#
# Author: Víctor Mayoral Vilches <victorma@xilinx.com>
import os

from colcon_core.plugin_system import satisfies_version
from colcon_krs.subverb import KRSSubverbExtensionPoint, get_vitis_dir


class KernelSubverb(KRSSubverbExtensionPoint):
    """Configure the Linux kernel type."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(KRSSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102
        argument = parser.add_argument(
            "type",
            nargs="?",
            help='Kernel type. Use "vanilla" key for a kernel with the default \n'
            'config, or "preempt_rt" key for a fully preemptible (PREEMPT_RT) kernel.',
        )
        try:
            from argcomplete.completers import ChoicesCompleter
        except ImportError:
            pass
        else:
            type_options = ["vanilla", "preempt_rt"]
            argument.completer = ChoicesCompleter(type_options)

        # remember the subparser to print usage in case no subverb is passed
        self.parser = parser

    def main(self, *, context):  # noqa: D102
        """Pick the corresponding kernel and configure it appropriately
        in the image.

        NOTE: Location, syntax and other related matters are defined
            within the `xilinx_firmware` package. Refer to it for more
            details.
        """
        if context.args.type == "vanilla":
            pass  # TODO: select vanilla
        elif context.args.type == "preempt_rt":
            pass  # TODO: select preempt_rt
        else:
            print(self.parser.format_usage())
            return "Error: No type provided"
