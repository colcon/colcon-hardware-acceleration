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

import sys

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

        argument = parser.add_argument("--fix", dest="fix_arg", action="store_true")

    def main(self, *, context):  # noqa: D102
        """Umount raw SD image"""

        # fix if hanging
        if context.args.fix_arg:
            run("sudo kpartx -d /dev/mapper/diskimage", shell=True, timeout=1)
            run("sudo dmsetup remove diskimage", shell=True, timeout=1)
            outs, errs = run("sudo losetup -f", shell=True, timeout=1)
            loopdevice = int(outs.replace("/dev/loop", ""))
            loopdevice -= 1
            print("loopdevice: " + str(loopdevice))
            run("sudo losetup -d /dev/loop" + str(loopdevice), shell=True, timeout=1)
            sys.exit(0)

        partition = 2
        if context.args.partition:
            partition = context.args.partition
        umount_rawimage(partition)
