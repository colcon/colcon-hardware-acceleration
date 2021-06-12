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

from colcon_core.plugin_system import satisfies_version
from colcon_krs.subverb import (
    KRSSubverbExtensionPoint,
    get_rawimage_path,
    mount_rawimage,
    umount_rawimage,
    run,
)
from colcon_krs import __version__


class UmountSubverb(KRSSubverbExtensionPoint):
    """Umount raw images."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(KRSSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102
        argument = parser.add_argument(
            "partition",
            type=int,
            nargs="?",
            help="Number of the partition to mount.",
        )

    def main(self, *, context):  # noqa: D102
        """Umount raw SD image"""
        partition = 2
        if context.args.partition:
            partition = context.args.partition
        umount_rawimage(partition)
