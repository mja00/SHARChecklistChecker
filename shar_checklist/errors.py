"""Typed exceptions so the CLI can map failures to friendly messages, not tracebacks."""


class SharError(Exception):
    """Base class for all errors raised by this package."""


class InvalidSaveError(SharError):
    """The file is not a readable SHAR save (bad magic, truncated, or misaligned)."""


class UnsupportedRegionError(SharError):
    """The save is a SHAR save but for a region this tool does not yet support."""
