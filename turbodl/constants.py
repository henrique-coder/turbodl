# Standard modules
from typing import Final, Literal


# Size constants
ONE_MB: Final[int] = 1048576
ONE_GB: Final[int] = 1073741824

# Chunk size constants
MIN_CHUNK_SIZE: Final[int] = 33554432  # 32 MB
MAX_CHUNK_SIZE: Final[int] = 268435456  # 256 MB
CHUNK_SIZE: Final[int] = 268435456  # 256 MB
MAX_BUFFER_SIZE: Final[int] = 2147483648  # 2 GB

# Connection constants
MAX_CONNECTIONS: Final[int] = 24
MIN_CONNECTIONS: Final[int] = 2

# File system constants
RAM_FILESYSTEMS: Final[frozenset[str]] = frozenset({"tmpfs", "ramfs", "devtmpfs"})

# HTTP headers
DEFAULT_HEADERS: Final[tuple[dict[str, str], ...]] = (
    {"Accept": "*/*"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"},
)
REQUIRED_HEADERS: Final[tuple[dict[str, str], ...]] = ({"Accept-Encoding": "identity"},)

# Units and values
YES_NO_VALUES: Final[tuple[Literal["no"], Literal["yes"]]] = ("no", "yes")  # "no", "yes"
