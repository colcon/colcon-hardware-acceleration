# Copyright (c) 2021, Xilinx®
# All rights reserved
#
# Author: Víctor Mayoral Vilches <victorma@xilinx.com>

import os
import subprocess
import sys

from colcon_core.logging import colcon_logger
from colcon_core.plugin_system import instantiate_extensions
from colcon_core.plugin_system import order_extensions_by_name
from colcon_krs.verb import gray, yellow, red, green

logger = colcon_logger.getChild(__name__)

# used by class below as the nth partition as
# as by external modules to generalize
mountpointn = "/tmp/sdcard_img_p"

# used by external modules
mountpoint1 = "/tmp/sdcard_img_p1"
mountpoint2 = "/tmp/sdcard_img_p2"

class KRSSubverbExtensionPoint:
    """
    The interface for vitis subverb extensions.
    A vitis subverb extension provides a subverb to the `vitis` verb of
    the command line tool.
    For each instance the attribute `SUBVERB_NAME` is being set to the basename
    of the entry point registering the extension.
    """

    """The version of the vitis subverb extension interface."""
    EXTENSION_POINT_VERSION = "1.0"

    def add_arguments(self, *, parser):
        """
        Add command line arguments specific to the subverb.
        The method is intended to be overridden in a subclass.

        :param parser: The argument parser
        """
        pass

    def main(self, *, context):
        """
        Execute the subverb extension logic.
        This method must be overridden in a subclass.

        :param context: The context providing the parsed command line arguments
        :returns: The return code
        """
        raise NotImplementedError()


def get_subverb_extensions():
    """
    Get the available subverb extensions.
    The extensions are ordered by their entry point name.

    :rtype: OrderedDict
    """
    extensions = instantiate_extensions(__name__)
    for name, extension in extensions.items():
        extension.SUBVERB_NAME = name
    return order_extensions_by_name(extensions)


def get_vitis_dir():
    """
    Get the path to the Vitis deployed software.
    Tries first the XILINX_VITIS env. variable and defaults
    to the current directory's PWD/xilinx/vitis.

    :rtype: String
    """
    if "XILINX_VITIS" in os.environ:
        vitis_dir = os.getenv("XILINX_VITIS")
    else:
        # take it from current directory
        current_dir = os.environ.get("PWD", "")
        vitis_dir = current_dir + "/xilinx/vitis"

    if os.path.exists(vitis_dir):
        return vitis_dir
    else:
        raise FileNotFoundError(
            vitis_dir,
            "consider setting XILINX_VITIS or running "
            + "this command from the root directory of the workspace "
            + "after xilinx's firmware has been deployed. \n"
            + "Try 'colcon build --merge-install' first.",
        )


def get_vivado_dir():
    """
    Get the path to the Vivado software.
    Tries first the XILINX_VIVADO env. variable and defaults
    to the current directory's PWD/xilinx/vivado.

    :rtype: String
    """
    if "XILINX_VIVADO" in os.environ:
        vivado_dir = os.getenv("XILINX_VIVADO")
    else:
        # take it from current directory
        current_dir = os.environ.get("PWD", "")
        vivado_dir = current_dir + "/xilinx/vivado"

    if os.path.exists(vivado_dir):
        return vivado_dir
    else:
        raise FileNotFoundError(
            vivado_dir,
            "consider setting XILINX_VIVADO or running "
            + "this command from the root directory of the workspace "
            + "after xilinx's firmware has been deployed. \n"
            + "Try 'colcon build --merge-install' first.",
        )


def get_vitis_hls_dir():
    """
    Get the path to the Vitis HLS deployed software.
    Tries first the XILINX_HLS env. variable and defaults
    to the current directory's PWD/xilinx/vitis_hls.

    :rtype: String
    """
    if "XILINX_HLS" in os.environ:
        vitis_hls_dir = os.getenv("XILINX_HLS")
    else:
        # take it from current directory
        current_dir = os.environ.get("PWD", "")
        vitis_hls_dir = current_dir + "/xilinx/vitis_hls"

    if os.path.exists(vitis_hls_dir):
        return vitis_hls_dir
    else:
        raise FileNotFoundError(
            vitis_hls_dir,
            "consider setting XILINX_HLS or running "
            + "this command from the root directory of the workspace "
            + "after xilinx's firmware has been deployed. \n"
            + "Try 'colcon build --merge-install' first.",
        )


def get_build_dir():
    """
    Get the path to the build directory

    :rtype: String
    """
    current_dir = os.environ.get("PWD", "")
    build_dir = current_dir + "/build"
    if os.path.exists(build_dir):
        return build_dir
    else:
        raise FileNotFoundError(
            build_dir,
            "consider running "
            + "this command from the root directory of the workspace "
            + "after building the ROS 2 workspace overlay. \n"
            + "Try 'colcon build --merge-install' first.",
        )


def get_firmware_dir():
    """
    Get the path to the Xilinx firmware deployed software

    NOTE: firmware is board-specific. Consult the README and/or change
    branch as per your hardware/board requirements.

    :rtype: String
    """
    current_dir = os.environ.get("PWD", "")
    firmware_dir = current_dir + "/xilinx/firmware"
    if os.path.exists(firmware_dir):
        return firmware_dir
    else:
        raise FileNotFoundError(
            firmware_dir,
            "consider running "
            + "this command from the root directory of the workspace "
            + "after xilinx's firmware has been deployed. \n"
            + "Try 'colcon build --merge-install' first.",
        )


def get_platform_dir():
    """
    Get the path to the Xilinx hardware platform deployed software. Usually
    lives within "<ros2_ws>/xilinx/firmware/platform".

    NOTE: platform is board-specific. Consult the README and/or change
    branch as per your hardware/board requirements.

    :rtype: String
    """
    current_dir = os.environ.get("PWD", "")
    platform_dir = current_dir + "/xilinx/firmware/platform"
    if os.path.exists(platform_dir):
        return platform_dir
    else:
        raise FileNotFoundError(
            platform_dir,
            "consider running "
            + "this command from the root directory of the workspace "
            + "after xilinx's firmware has been deployed. \n"
            + "Try 'colcon build --merge-install' first.",
        )


def get_install_dir(install_dir_input="install"):
    """
    Get the path to the install directory of the current ROS 2 overlay worksapce

    :rtype: String
    """
    current_dir = os.environ.get("PWD", "")
    install_dir = current_dir + "/" + install_dir_input
    if os.path.exists(install_dir):
        return install_dir
    else:
        raise FileNotFoundError(
            install_dir,
            "no install directory "
            + "found in the current workspace. Consider building it first. "
            + "Try 'colcon build --merge-install'.",
        )


def check_install_directory():
    """
    Check if the install directory exits in the root of the current workspace.

    :rtype: Bool
    """
    current_dir = os.environ.get("PWD", "")
    install_dir = current_dir + "/install"
    if os.path.exists(install_dir):
        return True
    else:
        return False


def get_rawimage_path(rawimage_filename="sd_card.img"):
    """
    Retring the full path of the raw image "sd_card.img" contained in the
    firmware directory if exists, None otherwise.

    Image is meant for both hardware and emulation. It usually lives in
    "<ros2_ws>/xilinx/firmware/sd_card.img".

    :rtype: String
    """
    firmware_dir = get_firmware_dir()
    rawimage_path = firmware_dir + "/" + rawimage_filename
    if os.path.exists(rawimage_path):
        return rawimage_path
    else:
        return None


def run(cmd, shell=False, timeout=1):
    """
    Spawns a new processe launching cmd, connect to their input/output/error pipes, and obtain their return codes.

    :param cmd: command split in the form of a list
    :returns: stdout
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=shell)
    try:
        outs, errs = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        outs, errs = proc.communicate()

    # decode, or None
    if outs:
        outs = outs.decode("utf-8").strip()
    else:
        outs = None

    if errs:
        errs = errs.decode("utf-8").strip()
    else:
        errs = None

    # # debug
    # gray(outs)
    # red(errs)

    return outs, errs


def mount_rawimage(rawimage_path, partition=1):
    """
    Mounts a disk image as provided by the parameter rawimage_path. Image is
    assumed to have two partitions and both are mounted respectively in
    /tmp/sdcard_img_p1 and /tmp/sdcard_img_p2.

    param: rawimage_path, the path of the raw disk image obtained by calling
    get_rawimage_path()

    param: partition number

    return: None
    """

    # TODO: transform this into a check that "partition" isn't greater
    # than the number of them in the actual raw image
    #
    # if partition != "p1" and partition != "p2":
    #     red("Partition value not accepted: " + partition)
    #     sys.exit(1)

    if not rawimage_path:
        red(
            "raw image file not found. Consider running "
            + "this command from the root directory of the workspace and build "
            + "the workspace first so that Xilinx packages deploy automatically "
            + "the image."
        )
        sys.exit(1)
    green("- Confirmed availability of raw image file at: " + rawimage_path)

    # fetch UNITS
    units = None
    cmd = "fdisk -l " + rawimage_path + " | grep 'Units' | awk '{print $8}'"
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

    # NOTE: when p1 is marked as boot in the partition table it needs
    # to be processed differently:
    #
    # # fetch STARTSECTORP1
    # startsectorp1 = None
    # cmd = "fdisk -l " + rawimage_path + " | grep 'img1' | awk '{print $3}'"
    # outs, errs = run(cmd, shell=True)
    # if outs:
    #     startsectorp1 = int(outs)
    # if not startsectorp1:
    #     red(
    #         "Something went wrong while fetching the raw image STARTSECTORP1.\n"
    #         + "Review the output: "
    #         + outs
    #     )
    #     sys.exit(1)

    # fetch STARTSECTORP2
    startsectorpn = None
    sectorpn = "img" + str(partition)
    cmd = "fdisk -l " + rawimage_path + " | grep '"+ sectorpn +"' | awk '{print $2}'"
    outs, errs = run(cmd, shell=True)
    if outs:
        startsectorpn = int(outs)
    if not startsectorpn:
        red(
            "Something went wrong while fetching the raw image STARTSECTOR for partition: "+ str(partition) +".\n"
            + "Review the output: "
            + outs
        )
        sys.exit(1)
    green("- Finished inspecting raw image, obtained UNITS and STARTSECTOR for partition: "+ str(partition) +".")

    # create mountpoints
    mountpointnth = mountpointn + str(partition)
    cmd = "mkdir -p " + mountpointnth
    outs, errs = run(cmd, shell=True)
    if errs:
        red(
            "Something went wrong while setting MOUNTPOINT.\n"
            + "Review the output: "
            + errs
        )
        sys.exit(1)

    # mount pnth
    cmd = (
        "sudo mount -o loop,offset="
        + str(units * startsectorpn)
        + " "
        + rawimage_path
        + " "
        + mountpointnth
    )
    outs, errs = run(
        cmd, shell=True, timeout=10
    )  # longer timeout, allow user to input password
    if errs:
        red(
            "Something went wrong while mounting partition: "+ str(partition) +".\n"
            + "Review the output: "
            + errs
        )
        sys.exit(1)
    green("- Image mounted successfully at: " + mountpointnth)


def umount_rawimage(partition=None):
    """
    Unmounts a disk image. Image paths are assumed to correspond with
    /tmp/sdcard_img_p1 and /tmp/sdcard_img_p2, etc.

    param (int): partition to umount
    """
    # syncs and umount both partitions, regardless of what's mounted (oversimplification)
    toumount = "1 and 2"
    if partition:
        cmd = "sync && sudo umount " + mountpointn + str(partition)
        toumount = str(partition)
    else:  # umount first and second by default
        cmd = "sync && sudo umount " + mountpoint1 + " && sudo umount " + mountpoint2
    outs, errs = run(cmd, shell=True, timeout=15)
    if errs:
        red(
            "Something went wrong while umounting the raw image partitions: " + toumount +".\n"
            + "Review the output: "
            + errs
        )
        sys.exit(1)
    green("- Umounted the raw image.")


def replace_kernel(kernel_filename):
    """
    Mount sd_card disk image in the workspace and replace kernel according
    to argument kernel_filename.

    NOTE: Refer to get_sdcard_img_dir() function for the location of
    the file
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


def add_kernel(kernel_filename):
    """
    Mount sd_card disk image in the workspace and add kernel according
    to argument kernel_filename.

    NOTE: As opposed to replace_kernel(), this function aims to allow
    adding additional kernel images (e.g. for Xen setups involving VMs
    with different kernels)

    NOTE 2: Refer to get_sdcard_img_dir() function for the location of
    the file
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

    # check that target kernel exists
    kernel_filename_path = firmware_dir + "/kernel/" + kernel_filename
    if not os.path.exists(kernel_filename_path):
        red("kernel file " + kernel_filename_path + " not found.")
        sys.exit(1)
    green("- Found kernel file " + kernel_filename_path)

    # copy the corresponding kernel file
    cmd = "sudo cp " + kernel_filename_path + " " + mountpoint1 + "/" + kernel_filename
    outs, errs = run(cmd, shell=True, timeout=15)
    if errs:
        red(
            "Something went wrong while replacig the kernel.\n"
            + "Review the output: "
            + errs
        )
        sys.exit(1)
    green("- Kernel added successfully (" + kernel_filename_path + ").")


def exists(file_path):
    """
    Check if file exists

    param file_path: absolute path of the file
    return: bool
    """
    if os.path.exists(file_path):
        return True
    else:
        return False
