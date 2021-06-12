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

from colcon_core.plugin_system import satisfies_version
from colcon_krs.subverb import KRSSubverbExtensionPoint, get_vitis_dir
from colcon_krs import __version__


class PlatformSubverb(KRSSubverbExtensionPoint):
    """Report the platform enabled in the deployed firmware."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(KRSSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def main(self, *, context):  # noqa: D102
        """Platform enabled

        NOTE: firmware is board-specific. Consult the README of
        acceleration_firmware_xilinx and/or change branch as per your
        hardware/board requirements.

        NOTE 2: Location, syntax and other related matters are defined
            within the `acceleration_firmware_xilinx` package. Refer to it for more
            details.
        """
        print(self.get_platform())
