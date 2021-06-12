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

import os
import sys

from colcon_core.plugin_system import satisfies_version
from colcon_krs.subverb import (
    KRSSubverbExtensionPoint,
    get_vitis_dir,
    get_build_dir,
    run,
    get_vivado_dir,
    get_vitis_hls_dir,
    get_platform_dir,
)
from colcon_krs.verb import yellow, red


class VppSubverb(KRSSubverbExtensionPoint):
    """Xilinx Vitis v++ compiler command.

    TODO: Document build process with v++. Document environmental variables

    NOTE 1: hardcoded build directory path

    TODO: REMOVE
        - compile: colcon vitis v++ "-c -t sw_emu --config ../../test/src/zcu102.cfg -k vadd -I../../test/src ../../test/src/vadd.cpp -o vadd.xo"
        - link: colcon vitis v++ "-l -t sw_emu --config ../../test/src/zcu102.cfg ./vadd.xo -o vadd.xclbin"
    """

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(KRSSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def add_arguments(self, *, parser):  # noqa: D102
        parser.description += (
            "\n\n"
            "The Vitis compiler is a standalone command line utility for both compiling "
            "kernel accelerator functions into Xilinx object (.xo) files, and linking "
            "them with other .xo files and supported platforms to build an FPGA binary. \n"
        )

        argument = parser.add_argument(
            "args",
            nargs="?",
            help='v++ compiler arguments provided as a String ("example arguments"). ',
        )
        try:
            from argcomplete.completers import ChoicesCompleter
        except ImportError:
            pass
        else:
            options = []
            argument.completer = ChoicesCompleter(options)

    def main(self, *, context):  # noqa: D102
        vitis_dir = get_vitis_dir()
        build_dir = get_build_dir()

        # create the "build/v++"" directory (if it doesn't exist already)
        # NOTE 1: hardcoded
        vpp_dir = build_dir + "/v++"
        cmd = "mkdir -p " + vpp_dir
        outs, errs = run(cmd, shell=True, timeout=20)
        if errs:
            red(
                "Something went wrong while creating the build/v++ directory.\n"
                + "Review the output: "
                + errs
            )
            sys.exit(1)

        # conform a command like, start including variables:
        #     XILINX_VIVADO=/home/erle/XRS/ros2_ws/xilinx/vivado PATH=/home/erle/XRS/ros2_ws/xilinx/vitis_hls/bin:$PATH
        #   /home/erle/XRS/ros2_ws/xilinx/vitis/bin/v++
        #
        cmd = ""
        cmd += "cd " + vpp_dir + " && "  # head to build dir
        cmd += " PLATFORM_REPO_PATHS=" + get_platform_dir()  # add target device dir
        cmd += " XILINX_VIVADO=" + get_vivado_dir()  # add Vivado dir
        cmd += " XILINX_VITIS=" + get_vitis_dir()  # add Vitis dir
        cmd += " XILINX_HLS=" + get_vitis_hls_dir()  # add Vitis HLS dir
        cmd += " PATH=$PATH:" + get_vitis_hls_dir() + "/bin"  # add HLS bin to path
        cmd += " " + get_vitis_dir() + "/bin/v++ "  # full path of v++ compiler

        # add args
        if context.args.args:
            cmd += context.args.args
        else:
            cmd += "--help"

        yellow(cmd)
        os.system(cmd)
