# Copyright 2022 Víctor Mayoral-Vilches
# Licensed under the Apache License, Version 2.0

# list hardware acceleration technology solutions available
import os

from colcon_core.plugin_system import satisfies_version
from colcon_hardware_acceleration.subverb import (
    AccelerationSubverbExtensionPoint,
    get_firmware_dir,
    run,
)
from colcon_hardware_acceleration import __version__
from colcon_hardware_acceleration.verb import green, yellow, red


def get_firmware_options():
    """Search the workspace for firmware options

    Looks into "acceleration/firmware"        
    """
    current_dir = os.environ.get("PWD", "")
    firmware_dir = current_dir + "/acceleration/firmware"
    cmd = "ls " + firmware_dir
    outs, errs = run(cmd, shell=True)

    firmware_options = outs.split("\n")
    if "select" in firmware_options: firmware_options.remove("select")
    return firmware_options


class ListSubverb(AccelerationSubverbExtensionPoint):
    """List supported firmware for hardware acceleration."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")


    def main(self, *, context):  # noqa: D102
        firmware_dir = get_firmware_dir()
        firmware_options = get_firmware_options()
        if firmware_dir:            
            target_firmware_dir = os.readlink(firmware_dir).split("/")[-1]
            for firm in firmware_options:
                if firm == target_firmware_dir:
                    green(firm + "*")
                else:
                    print(firm)
                
                # TODO: analyze each firmware directory and obtain more data
                #   from the files directly, maybe with --verbose option.
                #
                # Another approach could be to maintain a table including the
                #   support level of each firmware. This should be easier to 
                #   maintain and also more consistent with the REP.

        else:            
            print('Select firmware first with "colcon acceleration select '+ str(firmware_options) +'".')
