# Copyright 2022 Víctor Mayoral-Vilches
# Licensed under the Apache License, Version 2.0

from colcon_core.command import add_subparsers
from colcon_core.plugin_system import satisfies_version
from colcon_core.verb import VerbExtensionPoint
from colcon_hardware_acceleration.subverb import get_subverb_extensions


class AccelerationVerb(VerbExtensionPoint):
    """Manage hardware acceleration capabilities."""

    def __init__(self):  # noqa: D107
        super().__init__()
        satisfies_version(VerbExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")
        self._subparser = None

    def add_arguments(self, *, parser):  # noqa: D102
        # remember the subparser to print usage in case no subverb is passed
        self._subparser = parser

        # get subverb extensions and let them add their arguments
        subverb_extensions = get_subverb_extensions()
        add_subparsers(
            parser, "colcon acceleration",
            subverb_extensions, attribute="subverb_name"
        )

    def main(self, *, context):  # noqa: D102
        # error: no subverb provided
        if context.args.subverb_name is None:
            print(self._subparser.format_usage())
            return "Error: No subverb provided"
