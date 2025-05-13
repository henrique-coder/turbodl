# Standard modules
from importlib.metadata import version

# Local modules
from .core import TurboDL
from .exceptions import (
    DownloadError,
    DownloadInterruptedError,
    FFmpegNotFoundError,
    HashVerificationError,
    InvalidArgumentError,
    InvalidFileSizeError,
    MergeError,
    NotEnoughSpaceError,
    RemoteFileError,
    TurboDLError,
    UnidentifiedFileSizeError,
)


__all__: list[str] = [
    "TurboDL",
    "DownloadError",
    "DownloadInterruptedError",
    "FFmpegNotFoundError",
    "HashVerificationError",
    "InvalidArgumentError",
    "InvalidFileSizeError",
    "MergeError",
    "NotEnoughSpaceError",
    "RemoteFileError",
    "TurboDLError",
    "UnidentifiedFileSizeError",
]
__version__ = version("turbodl")
