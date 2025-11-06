from importlib.metadata import version

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
    UnidentifiedFileSizeError,
)


__version__ = version("turbodl")
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
    "UnidentifiedFileSizeError",
]
