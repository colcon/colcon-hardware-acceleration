# Copyright 2022 Víctor Mayoral-Vilches
# Licensed under the Apache License, Version 2.0

import os
import sys
import errno
from pathlib import Path

from colcon_core.plugin_system import satisfies_version
from colcon_hardware_acceleration.subverb import (
    AccelerationSubverbExtensionPoint,
    get_vitis_dir,
    get_rawimage_path,
    get_firmware_dir,
    mount_rawimage,
    umount_rawimage,
    run,
    mountpoint1,
    exists,
    copy_colcon_workspace,
    copy_libstdcppfs,
)
from colcon_hardware_acceleration.verb import green, yellow, red, gray


## No Xen, simple Linux kernel and rootfs-based
TEMPLATE_CONFIG = """\
MEMORY_START=0x0
MEMORY_END=0x80000000
DEVICE_TREE=system.dtb
BOOTBIN=BOOT.BIN
UBOOT_SCRIPT=boot.scr
DOM0_KERNEL=Image
DOM0_ROOTFS=rootfs.cpio.gz
NUM_DOMUS=0
"""


class LinuxSubverb(AccelerationSubverbExtensionPoint):
    """
    Configure the Linux kernel

    Typical use is as follows:
    - "colcon acceleration linux vanilla": select vanilla Linux kernel
    - "colcon acceleration linux preempt_rt": select low latency, fully preemptible Linux kernel
    """

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0"
        )

    def add_arguments(self, *, parser):  # noqa: D102
        argument = parser.add_argument(
            "type",
            nargs="?",
            choices=["preempt_rt", "vanilla"],
            help='Kernel type. Use "vanilla" key for a kernel with the default \n'
            'config, or "preempt_rt" key for a fully preemptible (PREEMPT_RT) kernel.',
        )

        argument = parser.add_argument(
            "rootfs",
            nargs="?",
            help="rootfs name relative to firmware_dir path. If not provided, defaults"
            " to rootfs.cpio.gz.",
        )

        # debug arg, show configuration and leave temp. dir (do not delete)
        argument = parser.add_argument("--debug", action="store_true", default=False)

        argument = parser.add_argument(
            "--install-dir",
            dest="install_dir",
            type=str,
            help="relative path to the workspace directory to deploy in emulation (typically 'install-*').",
        )

        # try:
        #     from argcomplete.completers import ChoicesCompleter
        # except ImportError:
        #     pass
        # else:
        #     type_options = ["vanilla", "preempt_rt"]
        #     argument.completer = ChoicesCompleter(type_options)

        # remember the subparser to print usage in case no subverb is passed
        self.parser = parser

    def replace_kernel(self, kernel_filename):
        """
        Mount sd_card disk image in the workspace and replace Linux kernel according
        to argument kernel_filename.

        NOTE: Refer to get_sdcard_img_dir() function for the location of
        the file
        """
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
                "Something went wrong while replacing the kernel.\n"
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

    def add_file(self, file):
        """
        Generic function to add desired file to the boot partition of the image
        from the firmware directory
        """
        firmware_dir = get_firmware_dir()

        # check that target device tree
        file_path = firmware_dir + "/" + file
        if not os.path.exists(file_path):
            red("file " + file_path + " not found.")
            sys.exit(1)
        green("- Found file: " + file_path)

        # copy the corresponding file
        cmd = "sudo cp " + file_path + " " + mountpoint1 + "/"
        outs, errs = run(cmd, shell=True, timeout=5)
        if errs:
            red(
                "Something went wrong while adding the file.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)
        green("- File added successfully (" + file_path + ").")

    def replace_bootbin(self, bootbin_file="BOOT.BIN.default"):
        """
        Replace BOOT.BIN file

        Checks if symlink exists
        """
        # # Add a security warning
        # yellow(
        #     "SECURITY WARNING: This class invokes explicitly a shell via the "
        #     "shell=True argument of the Python subprocess library, and uses "
        #     "admin privileges to manage raw disk images. It is the user's "
        #     "responsibility to ensure that all whitespace and metacharacters "
        #     "passed are quoted appropriately to avoid shell injection vulnerabilities."
        # )
        firmware_dir = get_firmware_dir()
        symlink_path = Path(firmware_dir + "/BOOT.BIN")

        # use symlink if exists and valid, else use default
        if symlink_path.is_symlink():
            try:
                os.stat(symlink_path)
            except OSError as e:
                if e.errno == errno.ENOENT:
                    print(
                        "path %s does not exist or is a broken symlink" % symlink_path
                    )
                    sys.exit(1)
                else:
                    raise e

            if not os.path.exists(symlink_path):
                red("BOOT.BIN file " + symlink_path + " not found.")
                sys.exit(1)
            green("- Found device BOOT.BIN file: " + str(symlink_path))

            # copy the corresponding file
            # NOTE: this will overwrite previous script
            # TODO: backup previous script if exists
            cmd = "sudo cp " + str(symlink_path) + " " + mountpoint1 + "/BOOT.BIN"
            outs, errs = run(cmd, shell=True, timeout=5)
            if errs:
                red(
                    "Something went wrong while replacing the device bootbin_file.\n"
                    + "Review the output: "
                    + errs
                )
                sys.exit(1)
            green(
                "- Device BOOT.BIN deployed successfully (" + str(symlink_path) + ")."
            )

        else:
            # check that target device bootbin_file
            device_bootbin_file_path = firmware_dir + "/bootbin/" + bootbin_file
            if not os.path.exists(device_bootbin_file_path):
                red("BOOT.BIN file " + device_bootbin_file_path + " not found.")
                sys.exit(1)
            green("- Found device BOOT.BIN file: " + device_bootbin_file_path)

            # copy the corresponding file
            # NOTE: this will overwrite previous script
            # TODO: backup previous script if exists
            cmd = (
                "sudo cp " + device_bootbin_file_path + " " + mountpoint1 + "/BOOT.BIN"
            )
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
            within the `acceleration_firmware_kv260` package. Refer to it for more
            details.
        """
        # Add a security warning
        yellow(
            "SECURITY WARNING: This class invokes explicitly a shell via the "
            "shell=True argument of the Python subprocess library, and uses "
            "admin privileges to manage raw disk images. It is the user's "
            "responsibility to ensure that all whitespace and metacharacters "
            "passed are quoted appropriately to avoid shell injection vulnerabilities."
        )

        #####################
        # re-create image
        #####################
        firmware_dir = get_firmware_dir()  # directory where firmware is

        # defaults firmware_dir + "/rootfs.cpio.gz"
        if context.args.rootfs:
            if exists(firmware_dir + "/" + context.args.rootfs):
                rootfs = firmware_dir + "/" + context.args.rootfs
            else:
                yellow(
                    "- rootfs "
                    + firmware_dir
                    + "/"
                    + context.args.rootfs
                    + ", doesn't exist. Defaulting to "
                    + firmware_dir
                    + "/rootfs.cpio.gz"
                )
                rootfs = firmware_dir + "/rootfs.cpio.gz"
        else:
            rootfs = firmware_dir + "/rootfs.cpio.gz"

        if not exists(rootfs):
            red("Rootfs at " + rootfs + " not found.")
            sys.exit(1)

        yellow("- Creating a new base image using " + rootfs + " ...")

        # re-using hypervisor tools, create a reference image
        auxdir = "/tmp/kernel"
        run("mkdir -p " + auxdir, shell=True, timeout=1)

        # save last image, delete rest
        if exists(firmware_dir + "/sd_card.img"):
            if exists(firmware_dir + "/sd_card.img.old"):
                run(
                    "sudo rm " + firmware_dir + "/sd_card.img.old",
                    shell=True,
                    timeout=1,
                )
                yellow("- Detected previous sd_card.img.old raw image, deleting.")

            run(
                "sudo mv "
                + firmware_dir
                + "/sd_card.img "
                + firmware_dir
                + "/sd_card.img.old",
                shell=True,
                timeout=1,
            )
            yellow(
                "- Detected previous sd_card.img raw image, moving to sd_card.img.old."
            )

        # copy vanilla artifacts by default
        # kernel
        run(
            "cp " + firmware_dir + "/kernel/Image " + auxdir + "/Image",
            shell=True,
            timeout=1,
        )
        # boot script
        run(
            "cp " + firmware_dir + "/boot_scripts/boot.scr.sd " + auxdir + "/boot.scr",
            shell=True,
            timeout=1,
        )
        # device tree
        run(
            "cp "
            + firmware_dir
            + "/device_tree/system.dtb.default "
            + auxdir
            + "/system.dtb",
            shell=True,
            timeout=1,
        )
        # boot bin
        run(
            "cp " + firmware_dir + "/bootbin/BOOT.BIN.default " + auxdir + "/BOOT.BIN",
            shell=True,
            timeout=1,
        )
        # rootfs
        run(
            "cp " + rootfs + " " + auxdir + "/rootfs.cpio.gz",
            shell=True,
            timeout=1,
        )

        # produce config
        config = open(auxdir + "/image.cfg", "w")
        config.truncate(0)  # delete previous content
        config.write(TEMPLATE_CONFIG)
        config.close()

        # create sd card image
        imagebuilder_dir = firmware_dir + "/imagebuilder"
        whoami, errs = run("whoami", shell=True, timeout=1)
        if errs:
            red(
                "Something went wrong while fetching username.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)
        # build image, add 500 MB of slack on each rootfs-based partition
        imagebuilder_path_diskimage = imagebuilder_dir + "/scripts/disk_image"
        cmd = (
            "cd "
            + auxdir
            + " && sudo bash "
            + imagebuilder_path_diskimage
            + " -c image.cfg -d . -t sd -w "
            + auxdir
            + " -o "
            + firmware_dir
            + "/sd_card.img "
            + "-s 500"
        )
        outs, errs = run(cmd, shell=True, timeout=60)
        if errs:
            red(
                "Something went wrong while creating sd card image.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)

        green("- Image successfully created")

        # permissions of the newly created image
        cmd = (
            "sudo chown " + whoami + ":" + whoami + " " + firmware_dir + "/sd_card.img"
        )
        outs, errs = run(cmd, shell=True)
        if errs:
            red(
                "Something went wrong while creating sd card image.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)

        # cleanup auxdir
        if not context.args.debug:
            run("sudo rm -r " + auxdir, shell=True, timeout=1)

        #####################
        # customize based on args
        #####################
        # now adapt image to the arguments passed
        if context.args.type == "vanilla" or not context.args.type:
            # mount p1
            rawimage_path = get_rawimage_path("sd_card.img")
            mount_rawimage(rawimage_path, 1)

            self.replace_kernel("Image")
            if self.get_board() == "kv260":
                self.replace_boot_script()
                self.add_file("ramdisk.cpio.gz.u-boot")
            self.replace_device_tree()
            self.replace_bootbin()

            # umount raw disk image, (technically, only p1)
            umount_rawimage(1)

        elif context.args.type == "preempt_rt":
            # mount p1
            rawimage_path = get_rawimage_path("sd_card.img")
            mount_rawimage(rawimage_path, 1)

            self.replace_kernel("Image_PREEMPT_RT")
            if self.get_board() == "kv260":
                self.replace_boot_script()
                self.add_file("ramdisk.cpio.gz.u-boot")
            self.replace_device_tree()
            self.replace_bootbin()

            # umount raw disk image, (technically, only p1)
            umount_rawimage(1)

        #####################
        # copy workspace to image
        #####################
        if context.args.install_dir:
            copy_colcon_workspace(context.args.install_dir)

        #####################
        # Fixes in rootfs
        #####################
        # Add libstdc++fs.a
        copy_libstdcppfs()
