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
# Licensed under the Apache License, Version 2.0
# 

# select across the ROS 2 hardware acceleration firmware solutions available

import os

from colcon_core.plugin_system import satisfies_version
from colcon_acceleration.subverb import (
    AccelerationSubverbExtensionPoint,    
)
from colcon_acceleration import __version__


class SelectSubverb(AccelerationSubverbExtensionPoint):
    """Select an existing firmware and default to it."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(AccelerationSubverbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

    def main(self, *, context):  # noqa: D102        
        raise NotImplementedError("Not implemented.")