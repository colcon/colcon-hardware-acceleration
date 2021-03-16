# Copyright (c) 2021, Xilinx®
# All rights reserved
#
# Author: Víctor Mayoral Vilches <victorma@xilinx.com>

import os
import subprocess

from colcon_core.logging import colcon_logger
from colcon_core.plugin_system import instantiate_extensions
from colcon_core.plugin_system import order_extensions_by_name
from colcon_krs.verb import gray, yellow, red

logger = colcon_logger.getChild(__name__)


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


def get_rawimage_path():
    """
    Retring the full path of the raw image "sd_card.img" contained in the firmware directory
    if exists, None otherwise.

    :rtype: String
    """
    firmware_dir = get_firmware_dir()
    rawimage_path = firmware_dir + "/sd_card.img"
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
    except TimeoutExpired:
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
