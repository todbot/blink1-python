# -*- coding: utf-8 -*-
"""
blink1 -- Python library for blink(1) USB RGB LED notification devices.

    from blink1 import Blink1

    b1 = Blink1()
    b1.fade_to_color(100, 'navy')
    b1.close()
"""

from importlib.metadata import PackageNotFoundError, version

from .blink1 import (
    PRODUCT_ID,
    VENDOR_ID,
    Blink1,
    Blink1ConnectionFailed,
    ColorCorrect,
    InvalidColor,
    UnknownWhitePoint,
)
from .blink1 import blink1 as blink1_ctx
from .kelvin import COLOR_TEMPERATURES, kelvin_to_rgb

try:
    __version__ = version("blink1")
except PackageNotFoundError:  # running from a source tree, not installed
    __version__ = "0.0.0+unknown"

# The context manager is exported as blink1_ctx rather than blink1. This
# package and its main module share the name, so binding `blink1` here to
# the function would make `import blink1.blink1 as m; m.Blink1` resolve to
# the function instead of the module. Use `from blink1.blink1 import blink1`
# for the original spelling.
__all__ = [
    "COLOR_TEMPERATURES",
    "PRODUCT_ID",
    "VENDOR_ID",
    "Blink1",
    "Blink1ConnectionFailed",
    "ColorCorrect",
    "InvalidColor",
    "UnknownWhitePoint",
    "__version__",
    "blink1_ctx",
    "kelvin_to_rgb",
]
