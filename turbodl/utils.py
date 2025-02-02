# Built-in imports
from math import ceil, log2, sqrt
from mimetypes import guess_extension as guess_mimetype_extension
from os import PathLike
from pathlib import Path
from typing import Final, Literal
from urllib.parse import unquote, urlparse

# Third-party imports
from httpx import Client, HTTPError, RemoteProtocolError
from psutil import disk_partitions, disk_usage
from rich.progress import DownloadColumn, ProgressColumn, Task, TransferSpeedColumn
from rich.text import Text
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

# Local imports
from .exceptions import InvalidArgumentError, OnlineRequestError


REQUIRED_HEADERS: Final[tuple[dict[str, str], ...]] = ({"Accept-Encoding": "identity"},)
DEFAULT_HEADERS: Final[tuple[dict[str, str], ...]] = (
    {"Accept": "*/*"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"},
)
ONE_GB: Final[int] = 1073741824
RAM_FILESYSTEMS: Final[frozenset[str]] = frozenset({"tmpfs", "ramfs"})
SIZE_UNITS: Final[tuple[str, ...]] = ("B", "KB", "MB", "GB", "TB")
BYTES_IN_UNIT: Final[int] = 1024
YES_NO_VALUES: Final[tuple[Literal["no"], Literal["yes"]]] = ("no", "yes")


class CustomDownloadColumn(DownloadColumn):
    def __init__(self, style: str | None = None) -> None:
        self.style = style

        super().__init__()

    def render(self, task: Task) -> Text:
        download_text = super().render(task)

        if self.style:
            download_text.stylize(self.style)

        return download_text


class CustomSpeedColumn(TransferSpeedColumn):
    def __init__(self, style: str | None = None) -> None:
        self.style = style

        super().__init__()

    def render(self, task: Task) -> Text:
        speed_text = super().render(task)

        if self.style:
            speed_text.stylize(self.style)

        return speed_text


class CustomTimeColumn(ProgressColumn):
    def __init__(
        self,
        elapsed_style: str = "white",
        remaining_style: str | None = None,
        parentheses_style: str | None = None,
        separator: str | None = None,
        separator_style: str | None = None,
    ) -> None:
        self.elapsed_style: str = elapsed_style
        self.remaining_style: str | None = remaining_style
        self.parentheses_style: str | None = parentheses_style
        self.separator: str | None = separator
        self.separator_style: str | None = separator_style or elapsed_style if separator else None

        super().__init__()

    def _format_time(self, seconds: float | None) -> str:
        if seconds is None or seconds < 0:
            return "0s"

        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts: list[str] = []

        if days > 0:
            parts.append(f"{days}d")

        if hours > 0:
            parts.append(f"{hours}h")

        if minutes > 0:
            parts.append(f"{minutes}m")

        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        return "".join(parts)

    def render(self, task: Task) -> Text:
        elapsed: float | None = task.finished_time if task.finished else task.elapsed
        remaining: float | None = task.time_remaining
        elapsed_str: str = self._format_time(elapsed)
        remaining_str: str = self._format_time(remaining)

        result = Text()
        result.append(f"{elapsed_str} elapsed", style=self.elapsed_style)

        if self.separator:
            result.append(f" {self.separator} ", style=self.separator_style)
        elif self.remaining_style:
            result.append(" ")

        if self.remaining_style:
            if self.parentheses_style:
                result.append("(", style=self.parentheses_style)

            result.append(f"{remaining_str} remaining", style=self.remaining_style)

            if self.parentheses_style:
                result.append(")", style=self.parentheses_style)

        return result


def validate_headers(headers: dict[str, str] | None) -> dict[str, str]:
    final_headers = {k: v for d in DEFAULT_HEADERS for k, v in d.items()}

    if headers:
        lowercase_required = {k.lower(): k for d in REQUIRED_HEADERS for k, v in d.items()}

        conflicts = [
            original_key
            for key, original_key in lowercase_required.items()
            if any(user_key.lower() == key for user_key in headers)
        ]

        if conflicts:
            raise InvalidArgumentError(f"Cannot override required headers: {', '.join(conflicts)}")

        final_headers.update(headers)

    for required_dict in REQUIRED_HEADERS:
        final_headers.update(required_dict)

    return final_headers


def get_filesystem_type(path: str | Path) -> str | None:
    path = Path(path).resolve()
    best_part = max(
        (part for part in disk_partitions(all=True) if path.as_posix().startswith(part.mountpoint)),
        key=lambda part: len(part.mountpoint),
        default=None,
    )

    return best_part.fstype if best_part else None


def has_available_space(path: str | PathLike, required_size_bytes: int, minimum_free_space_bytes: int = ONE_GB) -> bool:
    path = Path(path)
    required_space = required_size_bytes + minimum_free_space_bytes
    disk_usage_obj = disk_usage(path.parent.as_posix() if path.is_file() or not path.exists() else path.as_posix())

    return disk_usage_obj.free >= required_space


def is_ram_directory(path: str | PathLike) -> bool:
    filesystem_type = get_filesystem_type(path)

    return filesystem_type in RAM_FILESYSTEMS


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(HTTPError),
    reraise=True,
)
def fetch_file_info(http_client: Client, url: str) -> dict[str, str | int | None]:
    try:
        r = http_client.head(url, follow_redirects=True)
        r.raise_for_status()
    except RemoteProtocolError:
        return {
            "url": url,
            "filename": Path(unquote(urlparse(url).path)).name,
            "mimetype": "application/octet-stream",
            "size": None,
        }
    except HTTPError as e:
        raise OnlineRequestError(f"An error occurred while getting file info: {str(e)}") from e

    r_headers = r.headers
    content_length = int(r_headers.get("content-length", 0))
    content_length = None if content_length < 0 else content_length
    content_type = r_headers.get("content-type", "application/octet-stream").split(";")[0].strip()
    final_url = str(r.url)
    filename = None

    # Try to get filename from Content-Disposition header
    if content_disposition := r_headers.get("content-disposition"):
        if "filename*=" in content_disposition:
            filename = content_disposition.split("filename*=")[-1].split("'")[-1]
        elif "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip("\"'")

    # Try to get filename from final URL after redirects
    if not filename:
        filename = Path(unquote(urlparse(final_url).path)).name

    # Try to get filename from original URL if still not found
    if not filename:
        filename = Path(unquote(urlparse(url).path)).name

    # Add extension from mimetype if filename has no extension
    if filename and "." not in filename and (ext := guess_mimetype_extension(content_type)):
        filename = f"{filename}{ext}"

    # Use default name as last resort
    if not filename:
        filename = f"unknown_file{guess_mimetype_extension(content_type) or ''}"

    return {"url": final_url, "filename": filename, "mimetype": content_type, "size": content_length}


def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0.00 B"

    unit_index = min(len(SIZE_UNITS) - 1, int(size_bytes.bit_length() / 10))
    size = size_bytes / (BYTES_IN_UNIT**unit_index)

    return f"{size:.2f} {SIZE_UNITS[unit_index]}"


def bool_to_yes_no(value: bool) -> Literal["yes", "no"]:
    return YES_NO_VALUES[value]


def generate_chunk_ranges(size_bytes: int | None, max_connections: int) -> list[tuple[int, int]]:
    if size_bytes is None:
        return [(0, 0)]

    chunk_size = ceil(size_bytes / max_connections)

    ranges = []
    start = 0

    while size_bytes > 0:
        current_chunk = min(chunk_size, size_bytes)
        end = start + current_chunk - 1
        ranges.append((start, end))
        start = end + 1
        size_bytes -= current_chunk

    return ranges


def calculate_max_connections(size_bytes: int, connection_speed_mbps: float) -> int:
    size_mb = size_bytes / (1024 * 1024)

    beta = 5.6
    base_size = 1.0
    conn_float = beta * (log2(1 + size_mb / base_size) * sqrt(connection_speed_mbps / 100))

    return max(2, min(24, ceil(conn_float)))
