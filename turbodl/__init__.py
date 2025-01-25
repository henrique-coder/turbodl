# Built-in imports
from importlib.metadata import version

# Local imports
from .downloader import TurboDL
from .exceptions import (
    DownloadError,
    HashVerificationError,
    InsufficientSpaceError,
    InvalidArgumentError,
    OnlineRequestError,
    TurboDLError,
)

__all__: list[str] = [
    "DownloadError",
    "HashVerificationError",
    "InsufficientSpaceError",
    "InvalidArgumentError",
    "OnlineRequestError",
    "TurboDL",
    "TurboDLError",
]
__version__ = version("turbodl")
