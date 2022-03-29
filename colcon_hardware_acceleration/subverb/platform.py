# Copyright 2022 Víctor Mayoral-Vilches
# Licensed under the Apache License, Version 2.0

import os

from colcon_core.plugin_system import satisfies_version
from colcon_hardware_acceleration.subverb import AccelerationSubverbExtensionPoint, get_vitis_dir
from colcon_hardware_acceleration import __version__


class PlatformSubverb(AccelerationSubverbExtensionPoint):
    """Report the platform enabled in the deployed firmware."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def main(self, *, context):  # noqa: D102
        """Platform enabled

        NOTE: firmware is board-specific. Consult the README of
        acceleration_firmware_kv260 and/or change branch as per your
        hardware/board requirements.

        NOTE 2: Location, syntax and other related matters are defined
            within the `acceleration_firmware_kv260` package. Refer to it for more
            details.
        """
        print(self.get_platform())
