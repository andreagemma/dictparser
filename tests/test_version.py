from __future__ import annotations

import re

import dictparser
from dictparser._version import __version__


def test_public_version_uses_code_source() -> None:
    assert dictparser.__version__ == __version__
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:[a-zA-Z0-9.+-]*)?", __version__)
