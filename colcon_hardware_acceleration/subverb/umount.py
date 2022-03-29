# Copyright 2022 Víctor Mayoral-Vilches
# Licensed under the Apache License, Version 2.0

import sys

from colcon_core.plugin_system import satisfies_version
from colcon_hardware_acceleration.subverb import (
    AccelerationSubverbExtensionPoint,
    get_rawimage_path,
    mount_rawimage,
    umount_rawimage,
    run,
)
from colcon_hardware_acceleration import __version__


class UmountSubverb(AccelerationSubverbExtensionPoint):
    """Umount raw images."""

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
