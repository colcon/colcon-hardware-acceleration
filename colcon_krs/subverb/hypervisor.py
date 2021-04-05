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

# Default configuration, no additional VMs
DEFAULT_CONFIG = """\
MEMORY_START=0x0
MEMORY_END=0x80000000
DEVICE_TREE=system.dtb
XEN=xen
DOM0_KERNEL=Image
DOM0_RAMDISK=initrd.cpio
NUM_DOMUS=0
UBOOT_SOURCE=boot.source
UBOOT_SCRIPT=boot.scr
"""

# Default configuration, no additional VMs
DEFAULT_CONFIG2 = """\
MEMORY_START=0x0
MEMORY_END=0x80000000
DEVICE_TREE=system.dtb
XEN=xen
DOM0_KERNEL=Image
DOM0_RAMDISK=initrd.cpio
NUM_DOMUS=1
DOMU_KERNEL[0]="Image"
DOMU_RAMDISK[0]="initrd.cpio"
UBOOT_SOURCE=boot.source
UBOOT_SCRIPT=boot.scr
"""


class HypervisorSubverb(KRSSubverbExtensionPoint):
    """
    Configure the Xen hypervisor.

    Typical use is as follows:
    - "colcon krs hypervisor "
    """

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
        """
        Pick the corresponding kernel and configure it appropriately
        in the image.

        NOTE: Location, syntax and other related matters are defined
            within the `xilinx_firmware` package. Refer to it for more
            details.
        """
        # if context.args.type == "vanilla":
        #     pass
        # else:
        #     print(self.parser.format_usage())
        #     return "Error: No type provided"
        # copy the corresponding kernel file

        firmware_dir = get_firmware_dir()

        # create auxiliary directory for compiling all artifacts for the hypervisor
        auxdir = "/tmp/hypervisor"
        run("mkdir " + auxdir, shell=True, timeout=1)

        # copy the artifacts to auxiliary directory
        run(
            "cp " + firmware_dir + "/bootbin/BOOT.BIN.xen " + auxdir + "/BOOT.BIN",
            shell=True,
            timeout=1,
        )
        run(
            "cp " + firmware_dir + "/kernel/Image " + auxdir + "/Image",
            shell=True,
            timeout=1,
        )
        run("cp " + firmware_dir + "/xen " + auxdir + "/xen", shell=True, timeout=1)
        run(
            "cp "
            + firmware_dir
            + "/device_tree/system.dtb.xen "
            + auxdir
            + "/system.dtb",
            shell=True,
            timeout=1,
        )
        run(
            "cp " + firmware_dir + "/initrd.cpio " + auxdir + "/initrd.cpio",
            shell=True,
            timeout=1,
        )

        # produce config
        config = open(auxdir + "/xen.cfg", "w")
        config.truncate(0)  # delete previous content
        config.write(DEFAULT_CONFIG2)
        config.close()

        # generate boot script
        imagebuilder_dir = firmware_dir + "/imagebuilder"
        imagebuilder_path = imagebuilder_dir + "/scripts/uboot-script-gen"
        cmd = (
            "cd "
            + auxdir
            + " && bash "
            + imagebuilder_path
            + ' -c xen.cfg -d . -t "load mmc 0:1"'
        )
        outs, errs = run(cmd, shell=True, timeout=5)
        if errs:
            red("Something went wrong.\n" + "Review the output: " + errs)
            sys.exit(1)
        # print(outs)

        # mount sd_card image
        rawimage_path = get_rawimage_path("sd_card.img")
        mount_rawimage(rawimage_path, "p1")

        # copy all artifacts
        cmd = "sudo cp " + auxdir + "/* " + mountpoint1 + "/"
        outs, errs = run(cmd, shell=True, timeout=5)
        if errs:
            red(
                "Something went wrong while replacing the boot script.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)
        green("- Successfully copied all Xen artifacts.")

        # umount raw disk image, (technically, only p1)
        umount_rawimage("p1")

        # # cleanup auxdir
        # run("sudo rm -r " + auxdir, shell=True, timeout=1)
