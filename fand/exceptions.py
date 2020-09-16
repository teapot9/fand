"""Module for fand exceptions"""


class FandError(Exception):
    """Base class for all exceptions in fand"""


class GpioError(FandError):
    """Any GPIO related errors"""


class ShelfNotFoundError(FandError):
    """Given shelf name is unknown"""
