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
    {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
    },
    {"DNT": "1"},
    {"Connection": "keep-alive"},
    {"Cache-Control": "max-age=0"},
    {"Accept-Language": "en-US,en;q=0.9"},
    {"Sec-Fetch-Dest": "document"},
    {"Sec-Fetch-Mode": "navigate"},
    {"Sec-Fetch-Site": "none"},
    {"Sec-Fetch-User": "?1"},
    {"Upgrade-Insecure-Requests": "1"},
    {"sec-ch-ua": '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"'},
    {"sec-ch-ua-mobile": "?0"},
    {"sec-ch-ua-platform": '"Windows"'},
)
REQUIRED_HEADERS: Final[tuple[dict[str, str], ...]] = ({"Accept-Encoding": "identity"},)

# Units and values
YES_NO_VALUES: Final[tuple[Literal["no"], Literal["yes"]]] = ("no", "yes")

# Max RAM usage constants
MAX_RAM_USAGE: Final[float] = 0.20  # Maximum percentage of available RAM (e.g., 0.20 = 20%)
