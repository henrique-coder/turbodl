# Built-in imports
from math import ceil, log2, sqrt
from mimetypes import guess_extension as guess_mimetype_extension
from os import PathLike
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse

# Third-party imports
from httpx import Client, HTTPError, RemoteProtocolError
from psutil import disk_partitions, disk_usage
from rich.progress import DownloadColumn, ProgressColumn, Task, TransferSpeedColumn
from rich.text import Text
from tenacity import retry, stop_after_attempt, wait_exponential

# Local imports
from .exceptions import OnlineRequestError


class CustomDownloadColumn(DownloadColumn):
    """
    A DownloadColumn that allows custom styling.
    """

    def __init__(self, style: str | None = None) -> None:
        """
        Initialize the class.

        Args:
            style (str | None): The style to apply to the rendered text. If None, the default style will be used.
        """

        self.style = style

        super().__init__()

    def render(self, task: Task) -> Text:
        """
        Render the download speed.

        Args:
            task (Task): The task to render the download speed for.

        Returns:
            Text: The rendered download speed with the custom style applied.
        """

        download_text = super().render(task)

        # Apply the custom style if provided
        if self.style:
            download_text.stylize(self.style)

        return download_text


class CustomSpeedColumn(TransferSpeedColumn):
    """
    A TransferSpeedColumn that allows custom styling.
    """

    def __init__(self, style: str | None = None) -> None:
        """
        Initialize the class with optional styling.

        Args:
            style (str | None): The style to apply. If None, the default style will be used.
        """

        # Set the style attribute
        self.style = style

        # Call the parent class initializer
        super().__init__()

    def render(self, task: Task) -> Text:
        """
        Render the transfer speed.

        This method takes a Task as an argument, renders the transfer speed
        using the parent class, and then applies the custom style if provided.

        Args:
            task (Task): The task to render the transfer speed for.

        Returns:
            Text: The rendered transfer speed with the custom style applied.
        """

        # Get the transfer speed text from the parent class
        speed_text = super().render(task)

        # If a custom style is provided, apply it to the text
        if self.style:
            speed_text.stylize(self.style)

        # Return the rendered text
        return speed_text


class CustomTimeColumn(ProgressColumn):
    """
    Renders time elapsed and remaining in a dynamic format (e.g., '1h2m3s').
    """

    def __init__(
        self,
        elapsed_style: str = "white",
        remaining_style: str | None = None,
        parentheses_style: str | None = None,
        separator: str | None = None,
        separator_style: str | None = None,
    ) -> None:
        """
        Initialize the custom time column with the specified styles.

        Args:
            elapsed_style (str, optional): The style to apply to the elapsed time. Defaults to 'white'.
            remaining_style (str | None, optional): The style to apply to the remaining time. If None, the style will be the same as the elapsed style. Defaults to None.
            parentheses_style (str | None, optional): The style to apply to the parentheses around the remaining time. If None, the style will be the same as the elapsed style. Defaults to None.
            separator (str | None, optional): The separator to use between the elapsed and remaining times. If None, no separator will be used. Defaults to None.
            separator_style (str | None, optional): The style to apply to the separator. If None, the style will be the same as the elapsed style. Defaults to None.
        """

        self.elapsed_style: str = elapsed_style
        self.remaining_style: str | None = remaining_style
        self.parentheses_style: str | None = parentheses_style
        self.separator: str | None = separator
        self.separator_style: str | None = separator_style or elapsed_style if separator else None

        super().__init__()

    def _format_time(self, seconds: float | None) -> str:
        """
        Format the given time in seconds as a string.

        The time is formatted as a string with the following format:
        <days>d<hours>h<minutes>m<seconds>s

        If the time is negative or None, the string "0s" is returned.

        Args:
            seconds (float | None): The time in seconds to format.

        Returns:
            str: The formatted time string.
        """

        if seconds is None or seconds < 0:
            return "0s"

        # Calculate the number of days, hours, minutes and seconds
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Create a list of strings to represent the time
        parts: list[str] = []

        # Add the number of days to the list if there are any
        if days > 0:
            parts.append(f"{days}d")

        # Add the number of hours to the list if there are any
        if hours > 0:
            parts.append(f"{hours}h")

        # Add the number of minutes to the list if there are any
        if minutes > 0:
            parts.append(f"{minutes}m")

        # Add the number of seconds to the list if there are any
        # or if there are no other time units
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        # Join the list of strings and return the result
        return "".join(parts)

    def render(self, task: Task) -> Text:
        """
        Render the time elapsed and remaining as a string.

        This method takes a Task object as an argument and renders the time
        elapsed and remaining as a string. It uses the _format_time method to
        format the time values and the render method to render the text.

        Args:
            task (Task): The task to render the time for.

        Returns:
            Text: The rendered text with the elapsed and remaining time.
        """

        # Get the elapsed time
        elapsed: float | None = task.finished_time if task.finished else task.elapsed

        # Get the remaining time
        remaining: float | None = task.time_remaining

        # Format the elapsed time
        elapsed_str: str = self._format_time(elapsed)

        # Format the remaining time
        remaining_str: str = self._format_time(remaining)

        # Create the result text
        result = Text()

        # Add the elapsed time to the result
        result.append(f"{elapsed_str} elapsed", style=self.elapsed_style)

        # If there is a separator, add it
        if self.separator:
            result.append(f" {self.separator} ", style=self.separator_style)
        # Otherwise, add a space
        elif self.remaining_style:
            result.append(" ")

        # If there is a remaining time, add it
        if self.remaining_style:
            # If there are parentheses, add them
            if self.parentheses_style:
                result.append("(", style=self.parentheses_style)

            # Add the remaining time
            result.append(f"{remaining_str} remaining", style=self.remaining_style)

            # If there are parentheses, close them
            if self.parentheses_style:
                result.append(")", style=self.parentheses_style)

        # Return the result
        return result


def bool_to_yes_no(value: bool) -> Literal["yes", "no"]:
    """
    Convert a boolean value to a string value of "yes" or "no".

    Args:
        value (bool): The boolean value to convert.

    Returns:
        Literal["yes", "no"]: The string representation of the value.
    """

    return "yes" if value else "no"


def calculate_connections(file_size: int, connection_speed: float) -> int:
    """
    Calculate the optimal number of connections based on file size and connection speed.

    This method uses a sophisticated formula that considers:
    - Logarithmic scaling of file size
    - Square root scaling of connection speed
    - System resource optimization
    - Network overhead management

    Formula:
    conn = β * log2(1 + S / M) * sqrt(V / 100)

    Where:
    - S: File size in megabytes
    - V: Connection speed in megabits per second
    - M: Base size factor (1 megabyte)
    - β: Dynamic coefficient (5.6)

    The formula is designed to provide a good balance between using multiple connections
    to increase download speed and not overloading the system with too many connections.

    Args:
        file_size (int): The size of the file in bytes.
        connection_speed (float): Your connection speed in Mbps (megabits per second).

    Returns:
        int: The estimated optimal number of connections, capped between 2 and 24.
    """

    if file_size <= 2 * (1024 * 1024):  # If the file size is less than or equal to 2 MB
        return 2

    # Convert file size from bytes to megabytes
    file_size_mb = file_size / (1024 * 1024)

    # Dynamic coefficient for connection calculation
    # The value of 5.6 is chosen to balance the number of connections with the system resources
    beta = 5.6

    # Base size factor in megabytes
    # The value of 1 is chosen to provide a good balance between the file size and the number of connections
    base_size = 1.0

    # Calculate the number of connections using the formula
    # The formula is designed to provide a good balance between using multiple connections to increase download speed and not overloading the system with too many connections
    conn_float = beta * (log2(1 + file_size_mb / base_size) * sqrt(connection_speed / 100))

    # Ensure the number of connections is within the allowed range
    # The number of connections should be at least 2 to take advantage of multiple connections and should not exceed 24 to avoid overloading the system
    return max(2, min(24, ceil(conn_float)))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6), reraise=True)
def fetch_file_info(url: str, httpx_client: Client) -> dict[str, str | int] | None:
    """
    Fetch file information from the provided URL using an HTTP HEAD request.

    Args:
        url (str): The URL of the file to fetch information for.
        httpx_client (Client): An instance of httpx.Client to perform the HTTP request.

    Returns:
        dict[str, str | int] | None: A dictionary containing the file information, including URL, size, mimetype, and filename. Returns None if a RemoteProtocolError occurs.

    Raises:
        OnlineRequestError: If an HTTPError occurs during the request.
    """

    try:
        r = httpx_client.head(url)
    except RemoteProtocolError:
        return None
    except HTTPError as e:
        raise OnlineRequestError(f"An error occurred while getting file info: {str(e)}") from e

    r_headers = r.headers

    # Get the content length from headers, default to 0 if not present
    content_length = int(r_headers.get("content-length", 0))

    # Get the content type from headers, default to 'application/octet-stream' if not present
    content_type = r_headers.get("content-type", "application/octet-stream").split(";")[0].strip()

    # Get the content disposition from headers to extract the filename
    content_disposition = r_headers.get("content-disposition")
    filename = None

    if content_disposition:
        # RFC 5987 encoding for the filename
        if "filename*=" in content_disposition:
            filename = content_disposition.split("filename*=")[-1].split("'")[-1]
        # Standard encoding for the filename
        elif "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip("\"'")

    # If no filename is found, derive from URL path or use a default name
    if not filename:
        filename = Path(unquote(urlparse(url).path)).name or f"unknown_file{guess_mimetype_extension(content_type) or ''}"

    return {"url": r.url.__str__(), "size": content_length, "mimetype": content_type, "filename": filename}


def format_size(size_bytes: float) -> str:
    if size_bytes == 0:
        return "0.00 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0

    while size_bytes >= 1024.0 and unit_index < len(units) - 1:
        size_bytes /= 1024.0
        unit_index += 1

    return f"{size_bytes:.2f} {units[unit_index]}"


def get_chunk_ranges(
    total_size: int, max_connections: int | str | Literal["auto"], connection_speed: float
) -> list[tuple[int, int]]:
    """
    Calculate the optimal chunk ranges for downloading a file.

    This method divides the total file size into optimal chunks based on the number of connections.
    It returns a list of tuples, where each tuple contains the start and end byte indices for a chunk.

    Args:
        total_size (int): The total size of the file in bytes.
        max_connections (int | str | Literal["auto"]): The maximum number of connections to use for the download.
        connection_speed (float): Your connection speed in Mbps.

    Returns:
        list[tuple[int, int]]: A list of tuples containing the start and end indices of each chunk.
    """

    # If the total size is 0, return a single range starting and ending at 0
    if total_size == 0:
        return [(0, 0)]

    # Calculate the number of connections to use for the download
    if max_connections == "auto":
        max_connections = calculate_connections(total_size, connection_speed)

    max_connections = int(max_connections)

    # Calculate the size of each chunk
    chunk_size = ceil(total_size / max_connections)

    ranges = []
    start = 0

    # Create ranges for each chunk
    while total_size > 0:
        # Determine the size of the current chunk
        current_chunk = min(chunk_size, total_size)

        # Calculate the end index of the current chunk
        end = start + current_chunk - 1

        # Append the start and end indices as a tuple to the ranges list
        ranges.append((start, end))

        # Move the start index to the next chunk
        start = end + 1

        # Reduce the total size by the size of the current chunk
        total_size -= current_chunk

    return ranges


def get_filesystem_type(path: str | Path) -> str | None:
    """
    Get the filesystem type of a path.

    Args:
        path (str | Path): The path to get the filesystem type for.

    Returns:
        str | None: The filesystem type or None if the path is not a directory or does not exist.
    """

    path = Path(path).resolve()

    # Get the best matching mount point
    best_part = max(
        (part for part in disk_partitions(all=True) if path.as_posix().startswith(part.mountpoint)),
        key=lambda part: len(part.mountpoint),
        default=None,
    )

    # Return the filesystem type if the best match is not None
    return best_part.fstype if best_part else None


def has_available_space(path: str | PathLike, required_size: int, minimum_space: int = 1) -> bool:
    """
    Check if a path has enough free space to write a file of the given size.

    Args:
        path: The path to the file or directory to check.
        required_size: The minimum free space required in bytes.
        minimum_space: The minimum free space required in gigabytes (GB). Defaults to 1.

    Returns:
        True if the path has enough free space, False otherwise.
    """

    path = Path(path)

    # Calculate the required space in bytes
    required_space = required_size + (minimum_space * 1024 * 1024 * 1024)

    # Get the disk usage for the parent directory
    disk_usage_obj = disk_usage(path.parent.as_posix() if path.is_file() or not path.exists() else path.as_posix())

    # Return True if the path has enough free space
    return bool(disk_usage_obj.free >= required_space)


def looks_like_a_ram_directory(path: str | Path) -> bool:
    """
    Check if the given path is a temporary RAM-based filesystem.

    Args:
        path: The path to check.

    Returns:
        True if the path is a RAM-based filesystem, False otherwise.
    """

    # The following filesystem types are known to be RAM-based
    ram_filesystems = {"tmpfs", "ramfs", "devtmpfs"}

    # Get the filesystem type of the given path
    filesystem_type = get_filesystem_type(path)

    # Return True if the path is a RAM-based filesystem
    return filesystem_type in ram_filesystems
