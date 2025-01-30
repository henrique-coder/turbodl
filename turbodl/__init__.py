# Built-in imports
from importlib.metadata import version

# Local imports
from .core import TurboDL
from .exceptions import (
    DownloadError,
    HashVerificationError,
    InvalidArgumentError,
    NotEnoughSpaceError,
    OnlineRequestError,
    TurboDLError,
)

__all__: list[str] = [
    "TurboDL",
    "DownloadError",
    "HashVerificationError",
    "InvalidArgumentError",
    "NotEnoughSpaceError",
    "OnlineRequestError",
    "TurboDLError",
]
__version__ = version("turbodl")
