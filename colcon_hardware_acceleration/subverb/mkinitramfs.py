# Copyright 2022 Víctor Mayoral-Vilches
# Licensed under the Apache License, Version 2.0

import os
import sys

from colcon_core.plugin_system import satisfies_version
from colcon_hardware_acceleration.subverb import (
    AccelerationSubverbExtensionPoint,
    check_install_directory,
    get_rawimage_path,
    run,
    get_install_dir,
    get_firmware_dir,
    get_vitis_dir,
    get_vivado_dir,
    mount_rawimage,
    umount_rawimage,
)
from colcon_hardware_acceleration.verb import green, yellow, red


class MkinitramfsSubverb(AccelerationSubverbExtensionPoint):
    """Creates compressed cpio initramfs (ramdisks)

    This subverb grabs the current sd_card.img raw disk image, extracts the
    second partition (where the rootfs lives) and pushes it into a compressed
    cpio file.

    TODO: consider producing tar.gz files as well in the future if necessary.
    """

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102
        parser.add_argument(
            "out_file",
            help="Name of the resulting ramdisk (it should finish with .cpio.gz).",
        )

    def main(self, *, context):  # noqa: D102
        if not "cpio.gz" in context.args.out_file:
            red("Output file should be a compress cpio file, use .cpio.gz")
            sys.exit(1)

        rawimage_path = get_rawimage_path()
        mountpoint = mount_rawimage(rawimage_path, 2)
        firmware_dir = get_firmware_dir()  # directory where firmware is
        # do stuff in here

        # Inspired by Rob Landley's work around mkinitramfs
        cmd = (
            '(cd "'
            + mountpoint
            + '"; sudo find . | sudo cpio -o -H newc | gzip) > "'
            + firmware_dir
            + "/"
            + context.args.out_file
            + '"'
        )

        yellow(
            "- Creating ramdisk, this could take several minutes (depends of the disk size)..."
        )
        outs, errs = run(cmd, shell=True, timeout=300)
        if errs:
            red("Something went wrong.\n" + "Review the output: " + errs)
            sys.exit(1)

        umount_rawimage(2)
