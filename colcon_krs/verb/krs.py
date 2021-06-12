#    ____  ____
#   /   /\/   /
#  /___/  \  /   Copyright (c) 2021, Xilinx®.
#  \   \   \/    Author: Víctor Mayoral Vilches <victorma@xilinx.com>
#   \   \
#   /   /
#  /___/   /\
#  \   \  /  \
#   \___\/\___\
#

from colcon_core.command import add_subparsers
from colcon_core.plugin_system import satisfies_version
from colcon_core.verb import VerbExtensionPoint
from colcon_krs.subverb import get_subverb_extensions


class KRSVerb(VerbExtensionPoint):
    """Manage the Kria Robotics Stack (KRS) ROS 2 CLI."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(VerbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")
        self._subparser = None

    def add_arguments(self, *, parser):  # noqa: D102
        parser.description += (
            "\n\n"
            "The Xilinx's Kria Robotics Stack (KRS) is a complete integrated set\n"
            "of utilities, robotics software and hardware products built around\n"
            "ROS 2 to accelerate the development, certification and maintenance\n"
            "of industrial-grade robotic solutions.\n\n"
            "It includes extensions for the ROS 2 build system and meta build \n"
            "tools, reference accelerated actuator and sensor hardware robotics \n"
            "designs, evaluation and production System on Modules (SOMs) and \n"
            "multiple ready-for-PL robotics libraries that accelerate robotics\n"
            "perception, motion control, planning, navigation or simulation.\n"
        )

        # remember the subparser to print usage in case no subverb is passed
        self._subparser = parser

        # get subverb extensions and let them add their arguments
        subverb_extensions = get_subverb_extensions()
        add_subparsers(
            parser, "colcon krs", subverb_extensions, attribute="subverb_name"
        )

    def main(self, *, context):  # noqa: D102
        # error: no subverb provided
        if context.args.subverb_name is None:
            print(self._subparser.format_usage())
            return "Error: No subverb provided"
