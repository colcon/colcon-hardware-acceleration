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
# Licensed under the Apache License, Version 2.0
# 
import os

from colcon_core.plugin_system import satisfies_version
from colcon_acceleration.subverb import (
    AccelerationSubverbExtensionPoint,
    get_rawimage_path,
    mount_rawimage,
    umount_rawimage,
    run,
)
from colcon_acceleration import __version__


class MountSubverb(AccelerationSubverbExtensionPoint):
    """Mount raw images."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102
        argument = parser.add_argument(
            "partition",
            type=int,
            nargs="?",
            help="Number of the partition to mount.",
        )

    def main(self, *, context):  # noqa: D102
        """Mount raw SD image"""
        rawimage_path = get_rawimage_path("sd_card.img")
        partition = 2
        if context.args.partition:
            partition = context.args.partition
        mount_rawimage(rawimage_path, partition)
