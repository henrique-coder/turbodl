# Standard modules
from typing import Final, Literal


# Size constants
ONE_MB: Final[int] = 1024**2
ONE_GB: Final[int] = 1024**3

# Chunk size constants
MIN_CHUNK_SIZE: Final[int] = 16 * 1024**2
MAX_CHUNK_SIZE: Final[int] = 256 * 1024**2
CHUNK_SIZE: Final[int] = 256 * 1024**2
MAX_BUFFER_SIZE: Final[int] = 2 * 1024**3

# Connection constants
MAX_CONNECTIONS: Final[int] = 24
MIN_CONNECTIONS: Final[int] = 2

# File system constants
RAM_FILESYSTEMS: Final[frozenset[str]] = frozenset({"tmpfs", "ramfs", "devtmpfs"})

# HTTP headers
DEFAULT_HEADERS: Final[tuple[dict[str, str], ...]] = (
    {"Accept": "*/*"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"},
)
REQUIRED_HEADERS: Final[tuple[dict[str, str], ...]] = ({"Accept-Encoding": "identity"},)

# Units and values
YES_NO_VALUES: Final[tuple[Literal["no"], Literal["yes"]]] = ("no", "yes")

# Max RAM usage constants
MAX_RAM_USAGE: Final[float] = 0.30  # Maximum percentage of available RAM (e.g., 0.30 = 30%)
