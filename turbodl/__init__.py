# Standard modules
from importlib.metadata import version

# Local imports
from .core import TurboDL
from .exceptions import (
    DownloadError,
    DownloadInterruptedError,
    HashVerificationError,
    InvalidArgumentError,
    InvalidFileSizeError,
    NotEnoughSpaceError,
    RemoteFileError,
    TurboDLError,
)


__all__: list[str] = [
    "TurboDL",
    "DownloadError",
    "DownloadInterruptedError",
    "HashVerificationError",
    "InvalidArgumentError",
    "InvalidFileSizeError",
    "NotEnoughSpaceError",
    "RemoteFileError",
    "TurboDLError",
]
__version__ = version("turbodl")
