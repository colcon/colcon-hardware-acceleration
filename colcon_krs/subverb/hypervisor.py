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
    replace_kernel,
    add_kernel,
    exists,
)
from colcon_krs.verb import green, yellow, red, gray

# Default configuration, no additional VMs
# ## Only dom0
# DEFAULT_CONFIG = """\
# MEMORY_START=0x0
# MEMORY_END=0x80000000
# DEVICE_TREE=system.dtb
# XEN=xen
# DOM0_KERNEL=Image
# DOM0_RAMDISK=initrd.cpio
# NUM_DOMUS=0
# UBOOT_SOURCE=boot.source
# UBOOT_SCRIPT=boot.scr
# """

## dom0 + a dom0less machine with a busybox ramdisk
DEFAULT_CONFIG = """\
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

## Only dom0
TEMPLATE_CONFIG = """\
MEMORY_START=0x0
MEMORY_END=0x80000000
DEVICE_TREE=system.dtb
XEN=xen
UBOOT_SOURCE=boot.source
UBOOT_SCRIPT=boot.scr
"""


class HypervisorSubverb(KRSSubverbExtensionPoint):
    """
    Configure the Xen hypervisor.
    """

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(KRSSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102

        # debug arg, show configuration and leave temp. dir (do not delete)
        argument = parser.add_argument("--debug", action="store_true", default=False)

        # dom0 VM
        argument = parser.add_argument(
            "--dom0", action="store", dest="dom0_arg", choices=["preempt_rt", "vanilla"]
        )

        # domU VMs
        argument = parser.add_argument(
            "--domU",
            action="append",
            dest="domU_args",
            choices=["preempt_rt", "vanilla"],
            # nargs="+",
        )

        # dom0less VMs
        argument = parser.add_argument(
            "--dom0less",
            action="append",
            dest="dom0less_args",
            choices=["preempt_rt", "vanilla"],
        )

        # VMs ramdisks (dom0 is NOT included)
        argument = parser.add_argument(
            "--ramdisk",
            action="append",
            dest="ramdisk_args",
            help="ramdisks for VMs excluding dom0.",
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

    def default_hypervisor_setup(self, context):
        """
        Default image setup using:
            - dom0 and
            - dom0less machine with a busybox ramdisk
        """
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
        config.write(DEFAULT_CONFIG)
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

        if context.args.debug:
            gray(cmd)

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

        # cleanup auxdir
        if not context.args.debug:
            run("sudo rm -r " + auxdir, shell=True, timeout=1)

    def main(self, *, context):  # noqa: D102
        """
        Create a Xen configuration, produce boot scripts and deploy
        corresponding files into partitions.

        TODO: ramdisk selection is currently not implemented.

        NOTE: Location, syntax and other related matters are defined
            within the `xilinx_firmware` package. Refer to it for more
            details.
        """

        if context.args.domU_args and context.args.dom0less_args:
            red("Simultaneous use of domU and dom0less VMs not supported.")
            sys.exit(1)

        if not (
            context.args.dom0_arg
            or context.args.domU_args
            or context.args.dom0less_args
        ):
            self.default_hypervisor_setup(context)
            sys.exit(0)

        num_domus = 0  # NUM_DOMUS element in the configuration
        global TEMPLATE_CONFIG
        default_ramdisk = "initrd.cpio"

        # create auxiliary directory for compiling all artifacts for the hypervisor
        auxdir = "/tmp/hypervisor"
        run("mkdir " + auxdir, shell=True, timeout=1)

        firmware_dir = get_firmware_dir()  # directory where firmware is

        # define dom0
        if context.args.dom0_arg:
            # replace Image in boot partition and assign silly ramdisk (not used)
            if context.args.dom0_arg == "vanilla":
                # # directly to boot partition
                # replace_kernel("Image")

                # copy to auxdir
                run(
                    "cp " + firmware_dir + "/kernel/Image " + auxdir + "/Image",
                    shell=True,
                    timeout=1,
                )
                TEMPLATE_CONFIG += "DOM0_KERNEL=Image\n"

            elif context.args.dom0_arg == "preempt_rt":
                # # directly to boot partition
                # replace_kernel("Image_PREEMPT_RT")

                # copy to auxdir
                run(
                    "cp "
                    + firmware_dir
                    + "/kernel/Image_PREEMPT_RT "
                    + auxdir
                    + "/Image_PREEMPT_RT",
                    shell=True,
                    timeout=1,
                )
                TEMPLATE_CONFIG += "DOM0_KERNEL=Image_PREEMPT_RT\n"
            else:
                red("Unrecognized dom0 arg.")
                sys.exit(1)
            TEMPLATE_CONFIG += "DOM0_RAMDISK=initrd.cpio\n"  # ignored when using SD
            green("- Dom0 ramdisk assumed to reside in the second SD partition.")

            # process additional VMs
            if context.args.domU_args:
                # ensure ramdisks don't overrun domUs
                if context.args.ramdisk_args and (
                    len(context.args.domU_args) < len(context.args.ramdisk_args)
                ):
                    red(
                        "- More ramdisks provided than VMs. Note that dom0 should not be indicated."
                    )
                    sys.exit(1)
                # inform if ramdisks is lower than VMs
                if not context.args.ramdisk_args:
                    yellow(
                        "- No ramdisks provided. Defaulting to " + str(default_ramdisk)
                    )

                if context.args.ramdisk_args and (
                    len(context.args.domU_args) > len(context.args.ramdisk_args)
                ):
                    yellow(
                        "- Number of ramdisks is lower than domU VMs. "
                        "Last "
                        + str(
                            len(context.args.domU_args) - len(context.args.ramdisk_args)
                        )
                        + " VM will default to: "
                        + str(default_ramdisk)
                    )
                # iterate over each domU
                for domu in context.args.domU_args:
                    # define ramdisk for this domU, or default
                    if not context.args.ramdisk_args or (
                        num_domus >= len(context.args.ramdisk_args)
                    ):
                        ramdisk = default_ramdisk
                    else:
                        ramdisk = context.args.ramdisk_args[num_domus]

                    if domu == "vanilla":
                        # add_kernel("Image")  # directly to boot partition

                        # copy to auxdir
                        run(
                            "cp " + firmware_dir + "/kernel/Image " + auxdir + "/Image",
                            shell=True,
                            timeout=1,
                        )
                        TEMPLATE_CONFIG += (
                            "DOMU_KERNEL[" + str(num_domus) + ']="Image"\n'
                        )
                        TEMPLATE_CONFIG += (
                            "DOMU_RAMDISK["
                            + str(num_domus)
                            + ']="'
                            + str(ramdisk)
                            + '"\n'
                        )
                    elif domu == "preempt_rt":
                        # add_kernel("Image_PREEMPT_RT")  # directly to boot partition

                        # copy to auxdir
                        run(
                            "cp "
                            + firmware_dir
                            + "/kernel/Image_PREEMPT_RT "
                            + auxdir
                            + "/Image_PREEMPT_RT",
                            shell=True,
                            timeout=1,
                        )

                        TEMPLATE_CONFIG += (
                            "DOMU_KERNEL[" + str(num_domus) + ']="Image_PREEMPT_RT"\n'
                        )
                        TEMPLATE_CONFIG += (
                            "DOMU_RAMDISK["
                            + str(num_domus)
                            + ']="'
                            + str(ramdisk)
                            + '"\n'
                        )
                    else:
                        red("Unrecognized domU arg.")
                        sys.exit(1)
                    num_domus += 1

            elif context.args.dom0less_args:
                # ensure ramdisks don't overrun domUs
                if context.args.ramdisk_args and (
                    len(context.args.dom0less_args) < len(context.args.ramdisk_args)
                ):
                    red(
                        "- More ramdisks provided than VMs. Note that dom0 should not be indicated."
                    )
                    sys.exit(1)
                # inform if ramdisks is lower than VMs
                if not context.args.ramdisk_args:
                    yellow(
                        "- No ramdisks provided. Defaulting to " + str(default_ramdisk)
                    )

                if context.args.ramdisk_args and (
                    len(context.args.dom0less_args) > len(context.args.ramdisk_args)
                ):
                    yellow(
                        "- Number of ramdisks is lower than dom0less VMs. "
                        "Last "
                        + str(
                            len(context.args.dom0less_args)
                            - len(context.args.ramdisk_args)
                        )
                        + " VM will default to: "
                        + str(default_ramdisk)
                    )
                # iterate over each dom0less
                for dom0less in context.args.dom0less_args:
                    # define ramdisk for this dom0less, or default
                    if not context.args.ramdisk_args or (
                        num_domus >= len(context.args.ramdisk_args)
                    ):
                        ramdisk = default_ramdisk
                    else:
                        ramdisk = context.args.ramdisk_args[num_domus]

                    if dom0less == "vanilla":
                        # add_kernel("Image")

                        run(
                            "cp " + firmware_dir + "/kernel/Image " + auxdir + "/Image",
                            shell=True,
                            timeout=1,
                        )

                        TEMPLATE_CONFIG += (
                            "DOMU_KERNEL[" + str(num_domus) + ']="Image"\n'
                        )
                        TEMPLATE_CONFIG += (
                            "DOMU_RAMDISK["
                            + str(num_domus)
                            + ']="'
                            + str(ramdisk)
                            + '"\n'
                        )
                    elif dom0less == "preempt_rt":
                        # add_kernel("Image_PREEMPT_RT")
                        run(
                            "cp "
                            + firmware_dir
                            + "/kernel/Image_PREEMPT_RT "
                            + auxdir
                            + "/Image_PREEMPT_RT",
                            shell=True,
                            timeout=1,
                        )

                        TEMPLATE_CONFIG += (
                            "DOMU_KERNEL[" + str(num_domus) + ']="Image_PREEMPT_RT"\n'
                        )
                        TEMPLATE_CONFIG += (
                            "DOMU_RAMDISK["
                            + str(num_domus)
                            + ']="'
                            + str(ramdisk)
                            + '"\n'
                        )
                    else:
                        red("Unrecognized dom0less arg.")
                        sys.exit(1)
                    num_domus += 1

            # Add NUM_DOMUS at the end
            TEMPLATE_CONFIG += "NUM_DOMUS=" + str(num_domus) + "\n"

            if context.args.debug:
                gray("Debugging config file:")
                gray(TEMPLATE_CONFIG)

            # copy the artifacts to auxiliary directory
            run(
                "cp " + firmware_dir + "/bootbin/BOOT.BIN.xen " + auxdir + "/BOOT.BIN",
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

            # always copy (at least) initrd.cpio, which is the default one
            run(
                "cp " + firmware_dir + "/initrd.cpio " + auxdir + "/initrd.cpio",
                shell=True,
                timeout=1,
            )

            # add other ramdisks, if neccessary:
            if context.args.ramdisk_args:
                for ramdisk in context.args.ramdisk_args:
                    assert exists(firmware_dir + "/" + ramdisk)
                    run(
                        "cp "
                        + firmware_dir
                        + "/"
                        + ramdisk
                        + " "
                        + auxdir
                        + "/"
                        + ramdisk,
                        shell=True,
                        timeout=1,
                    )
                    green("- Copied to boot partition ramdisk: " + ramdisk)

            # produce config
            config = open(auxdir + "/xen.cfg", "w")
            config.truncate(0)  # delete previous content
            config.write(TEMPLATE_CONFIG)
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

            if context.args.debug:
                gray(cmd)

            outs, errs = run(cmd, shell=True, timeout=5)
            if errs:
                red("Something went wrong.\n" + "Review the output: " + errs)
                sys.exit(1)

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

            # cleanup auxdir
            if not context.args.debug:
                run("sudo rm -r " + auxdir, shell=True, timeout=1)

        else:
            red("No dom0 specified, doing nothing.")
