# Copyright (c) 2021, Xilinx®
# All rights reserved
#
# Author: Víctor Mayoral Vilches <victorma@xilinx.com>

import os
import sys

from colcon_core.plugin_system import satisfies_version
from colcon_krs.subverb import (
    KRSSubverbExtensionPoint,
    get_vitis_dir,
    get_rawimage_path,
    get_firmware_dir,
    mount_rawimage,
    umount_rawimage,
    run,
    mountpoint1,
)
from colcon_krs.verb import green, yellow, red


class KernelSubverb(KRSSubverbExtensionPoint):
    """
    Configure the Linux kernel type.

    Typical use is as follows:
    - "colcon krs kernel vanilla": select vanilla kernel
    - "colcon krs kernel preempt_rt": select low latency, fully preemptible kernel
    """

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(KRSSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102
        argument = parser.add_argument(
            "type",
            nargs="?",
            choices=["preempt_rt", "vanilla"],
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

    def replace_kernel(self, kernel_filename):
        """
        Mount sd_card disk image in the workspace and replace kernel according
        to argument kernel_filename.

        NOTE: Refer to get_sdcard_img_dir() function for the location of
        the file
        """
        # Add a security warning
        yellow(
            "SECURITY WARNING: This class invokes explicitly a shell via the "
            "shell=True argument of the Python subprocess library, and uses "
            "admin privileges to manage raw disk images. It is the user's "
            "responsibility to ensure that all whitespace and metacharacters "
            "passed are quoted appropriately to avoid shell injection vulnerabilities."
        )

        firmware_dir = get_firmware_dir()

        # check that target kernel exists
        kernel_filename_path = firmware_dir + "/kernel/" + kernel_filename
        if not os.path.exists(kernel_filename_path):
            red("kernel file " + kernel_filename_path + " not found.")
            sys.exit(1)
        green("- Found kernel file " + kernel_filename_path)

        # copy the corresponding kernel file
        cmd = "sudo cp " + kernel_filename_path + " " + mountpoint1 + "/Image"
        outs, errs = run(cmd, shell=True, timeout=15)
        if errs:
            red(
                "Something went wrong while replacig the kernel.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)
        green("- Kernel deployed successfully (" + kernel_filename_path + ").")

    def replace_boot_script(self, script="boot.scr.default"):
        """Replace boot script"""
        # # Add a security warning
        # yellow(
        #     "SECURITY WARNING: This class invokes explicitly a shell via the "
        #     "shell=True argument of the Python subprocess library, and uses "
        #     "admin privileges to manage raw disk images. It is the user's "
        #     "responsibility to ensure that all whitespace and metacharacters "
        #     "passed are quoted appropriately to avoid shell injection vulnerabilities."
        # )
        firmware_dir = get_firmware_dir()

        # check that target boot script exists
        boot_script_path = firmware_dir + "/boot_scripts/" + script
        if not os.path.exists(boot_script_path):
            red("boot script file " + boot_script_path + " not found.")
            sys.exit(1)
        green("- Found boot script file: " + boot_script_path)

        # copy the corresponding file
        # NOTE: this will overwrite previous script
        # TODO: backup previous script if exists
        cmd = "sudo cp " + boot_script_path + " " + mountpoint1 + "/boot.scr"
        outs, errs = run(cmd, shell=True, timeout=5)
        if errs:
            red(
                "Something went wrong while replacing the boot script.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)
        green("- Boot script deployed successfully (" + boot_script_path + ").")

    def replace_device_tree(self, tree="system.dtb.default"):
        """Replace device tree"""
        # # Add a security warning
        # yellow(
        #     "SECURITY WARNING: This class invokes explicitly a shell via the "
        #     "shell=True argument of the Python subprocess library, and uses "
        #     "admin privileges to manage raw disk images. It is the user's "
        #     "responsibility to ensure that all whitespace and metacharacters "
        #     "passed are quoted appropriately to avoid shell injection vulnerabilities."
        # )
        firmware_dir = get_firmware_dir()

        # check that target device tree
        device_tree_path = firmware_dir + "/device_tree/" + tree
        if not os.path.exists(device_tree_path):
            red("device tree file " + device_tree_path + " not found.")
            sys.exit(1)
        green("- Found device tree file: " + device_tree_path)

        # copy the corresponding file
        # NOTE: this will overwrite previous script
        # TODO: backup previous script if exists
        cmd = "sudo cp " + device_tree_path + " " + mountpoint1 + "/system.dtb"
        outs, errs = run(cmd, shell=True, timeout=5)
        if errs:
            red(
                "Something went wrong while replacing the device tree.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)
        green("- Device tree deployed successfully (" + device_tree_path + ").")

    def replace_bootbin(self, bootbin_file="BOOT.BIN.default"):
        """Replace BOOT.BIN file"""
        # # Add a security warning
        # yellow(
        #     "SECURITY WARNING: This class invokes explicitly a shell via the "
        #     "shell=True argument of the Python subprocess library, and uses "
        #     "admin privileges to manage raw disk images. It is the user's "
        #     "responsibility to ensure that all whitespace and metacharacters "
        #     "passed are quoted appropriately to avoid shell injection vulnerabilities."
        # )
        firmware_dir = get_firmware_dir()

        # check that target device bootbin_file
        device_bootbin_file_path = firmware_dir + "/bootbin/" + bootbin_file
        if not os.path.exists(device_bootbin_file_path):
            red("BOOT.BIN file " + device_bootbin_file_path + " not found.")
            sys.exit(1)
        green("- Found device BOOT.BIN file: " + device_bootbin_file_path)

        # copy the corresponding file
        # NOTE: this will overwrite previous script
        # TODO: backup previous script if exists
        cmd = "sudo cp " + device_bootbin_file_path + " " + mountpoint1 + "/BOOT.BIN"
        outs, errs = run(cmd, shell=True, timeout=5)
        if errs:
            red(
                "Something went wrong while replacing the device bootbin_file.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)
        green(
            "- Device BOOT.BIN deployed successfully ("
            + device_bootbin_file_path
            + ")."
        )

    def main(self, *, context):  # noqa: D102
        """Pick the corresponding kernel and configure it appropriately
        in the image.

        NOTE: Location, syntax and other related matters are defined
            within the `xilinx_firmware` package. Refer to it for more
            details.
        """
        if context.args.type == "vanilla":
            # mount p1
            rawimage_path = get_rawimage_path("sd_card.img")
            mount_rawimage(rawimage_path, "p1")

            self.replace_kernel("Image")
            self.replace_boot_script()
            self.replace_device_tree()
            self.replace_bootbin()

            # umount raw disk image, (technically, only p1)
            umount_rawimage("p1")

        elif context.args.type == "preempt_rt":
            # mount p1
            rawimage_path = get_rawimage_path("sd_card.img")
            mount_rawimage(rawimage_path, "p1")

            self.replace_kernel("Image_PREEMPT_RT")
            self.replace_boot_script()
            self.replace_device_tree()
            self.replace_bootbin()

            # umount raw disk image, (technically, only p1)
            umount_rawimage("p1")
        else:
            print(self.parser.format_usage())
            return "Error: No type provided"
