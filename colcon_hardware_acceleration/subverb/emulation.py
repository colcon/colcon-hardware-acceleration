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
    get_workspace_dir,
    create_ros2_overlay_script,
)
from colcon_hardware_acceleration.verb import green, yellow, red


class EmulationSubverb(AccelerationSubverbExtensionPoint):
    """Manage emulation capabilities.

    This extension does the following:
        1. verifies that the `<workspace>/install/` directory exists in the workspace.
            Resulting from past build processes.
        2. mounts p2 of the embedded raw image ("sd_card.img" file) available in deployed firmware
            and deploys the `<workspace>/install/` directory under "/<workspace-name>" in the rootfs.
        3. syncs and umount the raw image
        4. generates emulation files on the go
        5. launches emulator

    NOTE: The install/ directory in the workspace will be copied to
        "/<workspace-name>" in the image.

    NOTE 2: This class invokes explicitly a shell via shell=True of the Python subprocess library and uses admin,
    privileges to manage raw disk images. Tt is the user's responsibility to ensure that all whitespace and
    metacharacters passed are quoted appropriately to avoid shell injection vulnerabilities.
    """

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(
            AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0"
        )

    def add_arguments(self, *, parser):  # noqa: D102
        parser.description += (
            "\n\n"
            "Vitis offers two emulation targets for development, debugging and validation purposes.\n"
            "These two targets are:\n\n"
            "  - Software Emulation (sw_emu): The acceleration kernel code is compiled to run on the "
            "host processor, simulating its behavior. This approach thereby runs a simulated "
            "version of the accelerated code on top of an emulation, using a type 2 hypervisor (QEMU). "
            "This allows iterative algorithm refinement through fast build-and-run loops, useful for "
            "identifying syntax errors, performing source-level debugging of the accelerated kernel "
            "code running together with the application, while verifying the behavior of the system.\n"
            "\n"
            "  - Hardware Emulation (hw_emu) - The kernel code is compiled into a hardware model (RTL), "
            "which is run in a dedicated PL emulation. This approach thereby runs an emulated "
            "version of the accelerated code (emulation of PL) on top of yet another emulation, "
            "using a type 2 hypervisor (QEMU, emulating the HW). This build-and-run loop takes "
            "longer but provides a detailed, cycle-accurate view of the accelerated kernel activity. "
            "This target is useful for testing the functionality of the logic that will go in the "
            "FPGA and getting initial performance estimates.\n"
        )

        argument = parser.add_argument(
            "emulation_type",
            nargs="?",
            help='Emulation of board with either PL software simulation ("sw_emu" key) or PL software emulation ("hw_emu" key).',
        )
        argument = parser.add_argument(
            "install_dir",
            nargs="?",
            type=str,
            default="install",
            help="relative path to the workspace directory to deploy in emulation (typically 'install-*').",
        )
        argument = parser.add_argument(
            "--no-install",
            action="store_true",
            default=False,
            help="Do not copy install_dir (or default) to second partition",
            dest="no_install",
        )

        # try:
        #     from argcomplete.completers import ChoicesCompleter
        # except ImportError:
        #     pass
        # else:
        #     emulation_types = ["sw_emu", "hw_emu"]
        #     argument.completer = ChoicesCompleter(emulation_types)

    def gen_pmufile(self, emulation_files_dir, emulation_file_pmu):
        """
        Generate emulation arguments file for virtualizing the PMU, if
        it doesn't exist previously.

        NOTE: If files exists, does nothing. This allows developers to iterate/
        edit the arguments to the emulation.

        :param: emulation_files_dir: path to the emulation files directory
        :param: emulation_file_pmu: path of the file to create
        """

        if not os.path.exists(emulation_file_pmu):
            file_str = "-M" + "\n"
            file_str += "microblaze-fdt" + "\n"
            file_str += "-device" + "\n"
            file_str += "loader,file=" + emulation_files_dir + "/../pmufw.elf" + "\n"
            file_str += "-machine-path" + "\n"
            file_str += "." + "\n"
            file_str += "-display" + "\n"
            file_str += "none" + "\n"

            f = open(emulation_file_pmu, "w")
            f.truncate(0)  # delete previous content
            f.write(file_str)
            f.close()

    def gen_qemufile(self, emulation_files_dir, emulation_file_qemu):
        """
        Generate emulation arguments file for virtualizing the PS/PL side, if
        it doesn't exist previously.

        NOTE: If files exists, does nothing. This allows developers to iterate/
        edit the arguments to the emulation.

        NOTE 2: the configuration is set for the default dev. board, the ZCU102

        :param: emulation_files_dir: path to the emulation files directory
        :param: emulation_file_qemu: path of the file to create
        """
        if not os.path.exists(emulation_file_qemu):
            file_str = "-M" + "\n"
            file_str += "arm-generic-fdt" + "\n"
            file_str += "-serial" + "\n"
            file_str += "mon:stdio" + "\n"
            file_str += "-global" + "\n"
            file_str += "xlnx,zynqmp-boot.cpu-num=0" + "\n"
            file_str += "-global" + "\n"
            file_str += "xlnx,zynqmp-boot.use-pmufw=true" + "\n"
            file_str += "-net" + "\n"
            file_str += "nic" + "\n"
            file_str += "-net" + "\n"
            file_str += "nic" + "\n"
            file_str += "-net" + "\n"
            file_str += "nic" + "\n"
            file_str += "-net" + "\n"
            file_str += "nic" + "\n"
            file_str += "-net" + "\n"
            file_str += "user,hostfwd=tcp:127.0.0.1:2222-10.0.2.15:22" + "\n"
            file_str += "-m" + "\n"
            file_str += "4G" + "\n"
            file_str += "-device" + "\n"
            file_str += (
                "loader,file=" + emulation_files_dir + "/../bl31.elf,cpu-num=0" + "\n"
            )
            file_str += "-device" + "\n"
            file_str += "loader,file=" + emulation_files_dir + "/../u-boot.elf" + "\n"
            file_str += "-boot" + "\n"
            file_str += "mode=5" + "\n"

            f = open(emulation_file_qemu, "w")
            f.truncate(0)  # delete previous content
            f.write(file_str)
            f.close()

    def gen_qemufile_kv260(self, emulation_files_dir, emulation_file_qemu):
        """
        Generate emulation arguments file for virtualizing the PS/PL side of the KV260,
        if it doesn't exist previously.

        NOTE: If files exists, does nothing. This allows developers to iterate/
        edit the arguments to the emulation.

        :param: emulation_files_dir: path to the emulation files directory
        :param: emulation_file_qemu: path of the file to create
        """
        if not os.path.exists(emulation_file_qemu):

            file_str = "-M arm-generic-fdt\n"
            file_str += "-serial /dev/null -serial mon:stdio -display none" + "\n"
            file_str += (
                "-device loader,file="
                + emulation_files_dir
                + "/../bl31.elf,cpu-num=0"
                + "\n"
            )
            # file_str += "-device loader,file=" + emulation_files_dir + "/../ramdisk.cpio.gz.u-boot,addr=0x04000000,force-raw" + "\n"
            file_str += (
                "-device loader,file=" + emulation_files_dir + "/../u-boot.elf" + "\n"
            )
            # file_str += "-device loader,file=" + emulation_files_dir + "/../kernel/Image,addr=0x00200000,force-raw" + "\n"
            file_str += (
                "-device loader,file="
                + emulation_files_dir
                + "/../device_tree/u-boot.dtb,addr=0x00100000,force-raw"
                + "\n"
            )
            file_str += "-gdb tcp::9000" + "\n"
            # file_str += "-net nic -net nic -net nic -net nic,netdev=eth0 -netdev user,id=eth0,tftp=/tftpboot" + "\n"
            file_str += (
                "-net nic -net nic -net nic -net nic -net user,hostfwd=tcp:127.0.0.1:2222-10.0.2.15:22"
                + "\n"
            )
            file_str += (
                "-hw-dtb "
                + emulation_files_dir
                + "/../zynqmp-qemu-multiarch-arm.dtb"
                + "\n"
            )
            file_str += (
                "-global xlnx,zynqmp-boot.cpu-num=0 -global xlnx,zynqmp-boot.use-pmufw=true"
                + "\n"
            )
            file_str += "-m 4G" + "\n"

            f = open(emulation_file_qemu, "w")
            f.truncate(0)  # delete previous content
            f.write(file_str)
            f.close()

    def prepare_emulation(self, context):  # noqa: D102
        """
        Prepare the emulation

        param: context: superclass context containing arguments, etc.
        return: emulation_file_qemu, emulation_file_pmu, rawimage_path
        """
        # Add a security warning
        yellow(
            "SECURITY WARNING: This class invokes explicitly a shell via the shell=True argument of the Python"
            " subprocess library, and uses admin privileges to manage raw disk images. It is the user's "
            "responsibility to ensure that all whitespace and metacharacters passed are quoted appropriately"
            " to avoid shell injection vulnerabilities."
        )

        #########################
        # 1. verifies that the `<workspace>/install/` directory exists in the workspace.
        #########################
        if not check_install_directory():
            red(
                "workspace 'install' directory not found. Consider running "
                + "this command from the root directory of the workspace and build"
                + "the workspace first"
            )
            sys.exit(1)
        green("- Verified that install/ is available in the current colcon workspace")

        rawimage_path = get_rawimage_path()
        if not rawimage_path:
            red(
                "raw image file not found. Consider running "
                + "this command from the root directory of the workspace and build"
                + "the workspace first so that Xilinx packages deploy automatically"
                + "the image."
            )
            sys.exit(1)
        green("- Confirmed availability of raw image file at: " + rawimage_path)

        #########################
        # 2. mounts the embedded raw image ("sd_card.img" file) available in deployed firmware
        #     and deploys the `<workspace>/install/` directory under "/<workspace-name>"
        #     in the rootfs. Also, creates /opt/ros/foxy/setup.bash to facilitate transition.
        #
        # TODO: make setup.bash distro-agnostic
        #########################
        if not context.args.no_install:
            # fetch UNITS
            units = None
            cmd = (
                "fdisk -l "
                + rawimage_path
                + " | grep 'Units\|Unidades' | awk '{print $8}'"
            )
            outs, errs = run(cmd, shell=True)
            if outs:
                units = int(outs)
            if not units:
                red(
                    "Something went wrong while fetching the raw image UNITS.\n"
                    + "Review the output: "
                    + outs
                )
                sys.exit(1)

            # fetch STARTSECTORP1
            startsectorp1 = None
            cmd = "fdisk -l " + rawimage_path + " | grep 'img1' | awk '{print $3}'"
            outs, errs = run(cmd, shell=True)
            if outs:
                startsectorp1 = int(outs)
            if not startsectorp1:
                red(
                    "Something went wrong while fetching the raw image STARTSECTORP1.\n"
                    + "Review the output: "
                    + outs
                )
                sys.exit(1)

            # fetch STARTSECTORP2
            startsectorp2 = None
            cmd = "fdisk -l " + rawimage_path + " | grep 'img2' | awk '{print $2}'"
            outs, errs = run(cmd, shell=True)
            if outs:
                startsectorp2 = int(outs)
            if not startsectorp2:
                red(
                    "Something went wrong while fetching the raw image STARTSECTORP2.\n"
                    + "Review the output: "
                    + outs
                    if outs
                    else "None"
                )
                sys.exit(1)
            green(
                "- Finished inspecting raw image, obtained UNITS and STARTSECTOR P1/P2"
            )

            # define mountpoint and mount
            mountpoint = "/tmp/sdcard_img_p2"
            cmd = "mkdir -p " + mountpoint
            outs, errs = run(cmd, shell=True)
            if errs:
                red(
                    "Something went wrong while setting MOUNTPOINT.\n"
                    + "Review the output: "
                    + errs
                )
                sys.exit(1)
            cmd = (
                "sudo mount -o loop,offset="
                + str(units * startsectorp2)
                + " "
                + rawimage_path
                + " "
                + mountpoint
            )

            # # debug
            # print(cmd)

            outs, errs = run(
                cmd, shell=True, timeout=15
            )  # longer timeout, allow user to input password
            if errs:
                red(
                    "Something went wrong while mounting.\n"
                    + "Review the output: "
                    + errs
                )
                sys.exit(1)
            green("- Image mounted successfully at: " + mountpoint)

            workspace_dir = get_workspace_dir()
            # remove prior overlay colcon workspace files at "/<workspace_dir>",
            #  and copy the <ws>/install directory as such
            if os.path.exists(mountpoint + "/" + workspace_dir):
                cmd = "sudo rm -r " + mountpoint + "/" + workspace_dir + "/*"
                outs, errs = run(cmd, shell=True)
                if errs:
                    red(
                        "Something went wrong while removing image workspace.\n"
                        + "Review the output: "
                        + errs
                    )
                    sys.exit(1)
                green(
                    "- Successfully cleaned up prior overlay colcon workspace "
                    + "at: "
                    + mountpoint
                    + "/"
                    + workspace_dir
                )
            else:
                yellow(
                    "No prior overlay colcon workspace found "
                    + "at: "
                    + mountpoint
                    + "/"
                    + workspace_dir
                    + ", creating it."
                )
                cmd = "sudo mkdir " + mountpoint + "/" + workspace_dir
                outs, errs = run(cmd, shell=True)
                if errs:
                    red(
                        "Something went wrong while creating overlay colcon workspace.\n"
                        + "Review the output: "
                        + errs
                    )
                    sys.exit(1)

            install_dir = get_install_dir(context.args.install_dir)
            cmd = "sudo cp -r " + install_dir + "/* " + mountpoint + "/" + workspace_dir
            outs, errs = run(cmd, shell=True)
            if errs:
                red(
                    "Something went wrong while copying overlay colcon workspace to mountpoint.\n"
                    + "Review the output: "
                    + errs
                )
                sys.exit(1)
            green(
                "- Copied '"
                + context.args.install_dir
                + "' directory as a ROS 2 overlay workspace in the raw image"
                + " at location: /"
                + workspace_dir
                + "."
            )

            # Create setup.bash and copy to mountpoint in target_dir
            script_path = create_ros2_overlay_script()
            target_dir_embedded = "/opt/ros/foxy/"
            target_dir = mountpoint + target_dir_embedded

            cmd = "sudo mkdir -p " + target_dir
            outs, errs = run(cmd, shell=True)
            if errs:
                red(
                    "Something went wrong while creating "
                    + target_dir
                    + ".\n"
                    + "Review the output: "
                    + errs
                )
                sys.exit(1)

            cmd = "sudo cp " + script_path + " " + target_dir
            outs, errs = run(cmd, shell=True)
            if errs:
                red(
                    "Something went wrong while copying "
                    + script_path
                    + " to "
                    + target_dir
                    + ".\n"
                    + "Review the output: "
                    + errs
                )
                sys.exit(1)
            green(
                "- Created and copied in rootfs " + target_dir_embedded + "setup.bash."
            )

            #########################
            # 3. syncs and umount the raw image
            #########################
            cmd = "sync && sudo umount " + mountpoint
            outs, errs = run(cmd, shell=True, timeout=15)
            if errs:
                red(
                    "Something went wrong while umounting the raw image.\n"
                    + "Review the output: "
                    + errs
                )
                sys.exit(1)
            green("- Umounted the raw image.")

        #########################
        # 4. generates emulation files on-the-go
        #########################
        firmware_dir = get_firmware_dir()
        emulation_files_dir = firmware_dir + "/emulation"
        cmd = "mkdir -p " + emulation_files_dir
        outs, errs = run(cmd, shell=True)
        if errs:
            red(
                "Something went wrong while creating emulation directory in firmware.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)

        emulation_file_pmu = emulation_files_dir + "/pmu_args.txt"
        self.gen_pmufile(emulation_files_dir, emulation_file_pmu)

        emulation_file_qemu = emulation_files_dir + "/qemu_args.txt"
        if self.get_board() == "kv260":
            self.gen_qemufile_kv260(emulation_files_dir, emulation_file_qemu)
        else:  # default to zcu102
            self.gen_qemufile(emulation_files_dir, emulation_file_qemu)
        green("- Generated PMU and QEMU files.")

        return emulation_file_qemu, emulation_file_pmu, rawimage_path

    def sw_emu(self, context):  # noqa: D102
        """Compile and launch the "sw_emu" emulation target

        Args:
            context: superclass context containing arguments, etc.
        """
        (
            emulation_file_qemu,
            emulation_file_pmu,
            rawimage_path,
        ) = self.prepare_emulation(
            context
        )  # basic routine for emulation

        #########################
        # 5. launches emulator
        #########################
        yellow("- Launching emulation...")
        # set the path right...
        vitis_dir = get_vitis_dir()
        firmware_dir = get_firmware_dir()
        emulation_files_dir = firmware_dir + "/emulation"

        cmd = (
            "cd "
            + emulation_files_dir
            + " && "
            + vitis_dir
            + "/bin/launch_emulator -device-family ultrascale "
            "-target "
            + context.args.emulation_type
            + " -qemu-args-file "
            + emulation_file_qemu
            + " -pmc-args-file "
            + emulation_file_pmu
            + " -sd-card-image "
            + rawimage_path
            + " -enable-prep-target $*"
        )
        print(cmd)
        os.system(cmd)
        green("Finalized successfully.")

    def hw_emu(self, context):  # noqa: D102
        """Compile and launch the "hw_emu" emulation target

        Args:
            context: superclass context containing arguments, etc.
        """
        (
            emulation_file_qemu,
            emulation_file_pmu,
            rawimage_path,
        ) = self.prepare_emulation(
            context
        )  # basic routine for emulation

        # Add a second warning indicating that ONLY ONE kernel can be emulated every time
        yellow(
            "WARNING: Only one kernel can be emulated. Such kernel's package/sim directory should be symlinked"
            " into acceleration/firmware/select/emulation/sim directory."
        )

        platform = self.get_platform()

        # TODO: describe more pl_sim_dir
        pl_sim_dir = get_firmware_dir() + "/emulation/sim/behav_waveform/xsim"
        firmware_dir = get_firmware_dir()
        emulation_files_dir = firmware_dir + "/emulation"

        #########################
        # 5. launches emulator
        #########################
        yellow("- Launching emulation...")
        # set the path right...
        vitis_dir = get_vitis_dir()
        cmd = (
            "cd "
            + emulation_files_dir
            + " && "
            + " PATH=$PATH:"
            + get_vivado_dir()
            + "/bin "
            + vitis_dir
            + "/bin/launch_emulator -device-family ultrascale "
            "-target "
            + context.args.emulation_type
            + " -qemu-args-file "
            + emulation_file_qemu
            + " -pmc-args-file "
            + emulation_file_pmu
            + " -pl-sim-dir "
            + pl_sim_dir
            + " -sd-card-image "
            + rawimage_path
            + " -enable-prep-target "
            + " -xtlm-log-state WAVEFORM_AND_LOG "
            + " -platform-name "
            + platform
            + " "
            + " $* "
        )
        os.system(cmd)
        green("Finalized successfully.")

    def main(self, *, context):  # noqa: D102
        if not context.args.emulation_type:
            # defaults to "sw_emu"
            context.args.emulation_type = "sw_emu"
        if context.args.emulation_type == "sw_emu":
            self.sw_emu(context)
        elif context.args.emulation_type == "hw_emu":
            self.hw_emu(context)
        else:
            red(
                "Unknown [emulation_type] argument: "
                + context.args.emulation_type
                + "\n"
                + "See colcon vitis emulation --help."
            )
            sys.exit(1)
