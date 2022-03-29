# Copyright 2022 Víctor Mayoral-Vilches
# Licensed under the Apache License, Version 2.0

# select across the ROS 2 hardware acceleration firmware solutions available

import os

from colcon_core.plugin_system import satisfies_version
from colcon_hardware_acceleration.subverb import (
    AccelerationSubverbExtensionPoint,
    run,
)
from colcon_hardware_acceleration import __version__
from colcon_hardware_acceleration.verb import green, yellow, red
from colcon_hardware_acceleration.subverb.list import get_firmware_options


class SelectSubverb(AccelerationSubverbExtensionPoint):
    """Select an existing firmware and default to it."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")


    def add_arguments(self, *, parser):  # noqa: D102
        argument = parser.add_argument(
            "firmware",
            type=str,
            nargs=1,
            help="Firmware to select."
        )


    def main(self, *, context):  # noqa: D102
        # print(context.args.firmware)
        
        firmware_candidate = str(context.args.firmware[0])

        # unlink previously selected firmware, if exists
        current_dir = os.environ.get("PWD", "")
        firmware_dir = current_dir + "/acceleration/firmware/select"
        target_firmware_dir = current_dir + "/acceleration/firmware/" + firmware_candidate
        if os.path.exists(firmware_dir):
            cmd = "unlink " + firmware_dir
            outs, errs = run(cmd, shell=True)

        firmware_options = get_firmware_options()
        if firmware_candidate in firmware_options:
            cmd = "ln -s " + target_firmware_dir + " " + firmware_dir
            outs, errs = run(cmd, shell=True)
        else:
            red("'" + firmware_candidate + "' not found among firmware deployed. Try: " + str(firmware_options))
