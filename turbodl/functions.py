# Built-in imports
from math import ceil, log2, sqrt
from mimetypes import guess_extension as guess_mimetype_extension
from os import PathLike
from pathlib import Path
from typing import Any, Literal
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
        Initialize the CustomDownloadColumn instance.

        Args:
            style (str | None): The style to apply to the download text. Defaults to None.
        """

        # Store the style for the download text
        self.style = style

        # Call the superclass constructor
        super().__init__()

    def render(self, task: Task) -> Text:
        """
        Render the download text with custom styling.

        This method retrieves the base download text from the superclass,
        applies the custom style if specified, and returns the styled text.

        Args:
            task (Task): The task for which the download text is being rendered.

        Returns:
            Text: The rendered download text with optional custom styling.
        """

        # Get the base download text from the superclass
        download_text = super().render(task)

        # Apply custom style if specified
        if self.style:
            download_text.stylize(self.style)

        # Return the styled download text
        return download_text


class CustomSpeedColumn(TransferSpeedColumn):
    """
    A TransferSpeedColumn that allows custom styling.
    """

    def __init__(self, style: str | None = None) -> None:
        """
        Initialize the CustomSpeedColumn instance.

        Args:
            style (str | None): The style to apply to the speed text. Defaults to None.
        """

        # Store the style for the speed text
        self.style = style

        # Call the superclass constructor
        super().__init__()

    def render(self, task: Task) -> Text:
        """
        Render the speed column with custom styling.

        This method retrieves the base speed text from the superclass,
        applies the custom style if provided, and returns the styled text.

        Args:
            task (Task): The task for which the speed is being rendered.

        Returns:
            Text: The rendered speed text with optional custom styling.
        """

        # Get the base speed text from the superclass
        speed_text = super().render(task)

        # Apply custom style if specified
        if self.style:
            speed_text.stylize(self.style)

        # Return the styled speed text
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
        Initialize the CustomTimeColumn instance.

        This class is used as a column in the progress bar to display the elapsed and remaining time.

        Args:
            elapsed_style (str, optional): The style to use for the elapsed time. Defaults to "white".
            remaining_style (str | None, optional): The style to use for the remaining time. Defaults to None.
            parentheses_style (str | None, optional): The style to use for parentheses. Defaults to None.
            separator (str | None, optional): Text to separate elapsed and remaining time. Only included if not None. Defaults to None.
            separator_style (str | None, optional): The style to use for separator. If None and separator is not None, uses elapsed_style. Defaults to None.
        """

        # Store the styles for the elapsed and remaining times
        self.elapsed_style: str = elapsed_style
        self.remaining_style: str | None = remaining_style
        self.parentheses_style: str | None = parentheses_style
        self.separator: str | None = separator
        self.separator_style: str | None = separator_style or elapsed_style if separator else None

        # Initialize the CustomTimeColumn instance
        super().__init__()

    def _format_time(self, seconds: float | None) -> str:
        """Format seconds into a human-readable string.

        Args:
            seconds (float | None): Number of seconds to format. If None or negative, returns '0s'.

        Returns:
            str: Formatted time string (e.g., '1h2m3s', '5m30s', '45s').

        This function takes a number of seconds and formats it into a human-readable string.
        If the input is None or negative, it returns '0s'.
        """

        # If the input is None or negative, return '0s'
        if seconds is None or seconds < 0:
            return "0s"

        # Calculate the days, hours, minutes, and seconds
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        # Initialize an empty list to store the time parts
        parts: list[str] = []

        # If the number of days is greater than 0, add it to the parts list
        if days > 0:
            parts.append(f"{days}d")
        # If the number of hours is greater than 0, add it to the parts list
        if hours > 0:
            parts.append(f"{hours}h")
        # If the number of minutes is greater than 0, add it to the parts list
        if minutes > 0:
            parts.append(f"{minutes}m")
        # If the number of seconds is greater than 0 or if the parts list is empty, add it to the parts list
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        # Join the parts list into a single string and return it
        return "".join(parts)

    def render(self, task: Task) -> Text:
        """
        Render the time column.

        This method formats the elapsed time and estimated remaining time for a
        progress task and returns a Text object containing the formatted string.

        Args:
            task (Task): The progress task containing timing information.

        Returns:
            Text: A Text object containing the formatted time string.
        """

        # Get the elapsed and remaining times
        elapsed: float | None = task.finished_time if task.finished else task.elapsed
        remaining: float | None = task.time_remaining

        # Format the times
        elapsed_str: str = self._format_time(elapsed)
        remaining_str: str = self._format_time(remaining)

        # Create Text objects with different styles
        result = Text()

        # Add elapsed time
        result.append(f"{elapsed_str} elapsed", style=self.elapsed_style)

        # Add separator if provided
        if self.separator:
            result.append(f" {self.separator} ", style=self.separator_style)
        elif self.remaining_style:  # Add space if no separator but has remaining time
            result.append(" ")

        # Add remaining time with or without parentheses
        if self.remaining_style:
            if self.parentheses_style:
                result.append("(", style=self.parentheses_style)

            result.append(f"{remaining_str} remaining", style=self.remaining_style)

            if self.parentheses_style:
                result.append(")", style=self.parentheses_style)

        # Return the rendered Text object
        return result


def bool_to_yes_no(value: bool) -> Literal["yes", "no"]:
    """
    Convert boolean value to 'yes' or 'no' string.

    Args:
        value (bool): The boolean value to be converted.

    Returns:
        Literal["yes", "no"]: The converted string ('yes' or 'no').
    """

    # Return 'yes' if the boolean value is True, otherwise return 'no'
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
    - S: File size in MB
    - V: Connection speed in Mbps
    - M: Base size factor (1 MB)
    - β: Dynamic coefficient (5.6)

    Args:
        file_size (int): The size of the file in bytes.
        connection_speed (float): Your connection speed in Mbps.

    Returns:
        int: The estimated optimal number of connections, capped between 2 and 24.
    """

    # Convert file size from bytes to megabytes
    file_size_mb = file_size / (1024 * 1024)

    # Dynamic coefficient for connection calculation
    beta = 5.6

    # Base size factor in MB
    base_size = 1.0

    # Calculate the number of connections using the formula
    conn_float = beta * log2(1 + file_size_mb / base_size) * sqrt(connection_speed / 100)

    # Ensure the number of connections is within the allowed range
    return max(2, min(24, ceil(conn_float)))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6), reraise=True)
def fetch_file_info(url: str, httpx_client: Client, headers: dict[str, Any]) -> dict[str, str | int] | None:
    """
    Get information about the file to be downloaded.

    This method sends a HEAD request to the provided URL and retrieves the file size, mimetype, and filename from the response headers.
    It will retry the request up to 3 times if it fails.

    Args:
        url (str): The URL of the file to be downloaded.
        httpx_client (Client): The HTTPX client to use for the request.
        headers (dict[str, Any]): The headers to include in the request.

    Returns:
        dict[str, str | int] | None: A dictionary containing the file size, mimetype, and filename, or None if the request fails.

    Raises:
        OnlineRequestError: If the request fails due to an HTTP error.
    """

    try:
        # Send a HEAD request to the URL to get the file information
        r = httpx_client.head(url, headers=headers)
    except RemoteProtocolError:
        # If the request fails due to a remote protocol error, return None
        return None
    except HTTPError as e:
        # If the request fails due to an HTTP error, raise a OnlineRequestError
        raise OnlineRequestError(f"An error occurred while getting file info: {str(e)}") from e

    # Get the headers from the response
    r_headers = r.headers

    # Get the content length from the headers
    content_length = int(r_headers.get("content-length", 0))

    # Get the content type from the headers
    content_type = r_headers.get("content-type", "application/octet-stream").split(";")[0].strip()

    # Get the filename from the content disposition header
    content_disposition = r_headers.get("content-disposition")
    filename = None

    if content_disposition:
        if "filename*=" in content_disposition:
            filename = content_disposition.split("filename*=")[-1].split("'")[-1]
        elif "filename=" in content_disposition:
            filename = content_disposition.split("filename=")[-1].strip("\"'")

    if not filename:
        # If filename is not found, use the URL path as the filename
        filename = Path(unquote(urlparse(url).path)).name or f"unknown_file{guess_mimetype_extension(content_type) or ''}"

    # Return the file information
    return {"size": content_length, "mimetype": content_type, "filename": filename}


def format_size(size_bytes: int) -> str:
    """
    Format size in bytes to human readable format.

    This function takes an integer representing a size in bytes and returns a string representation of the size, using the appropriate unit (B, KB, MB, GB, TB).

    Args:
        size_bytes (int): The size in bytes to format.

    Returns:
        str: A string representation of the size in bytes, using the appropriate unit (B, KB, MB, GB, TB).
    """

    if size_bytes == 0:
        return "0.00 B"

    # List of units to use for formatting
    units = ["B", "KB", "MB", "GB", "TB"]

    # Size in bytes as a float
    size = float(size_bytes)

    # Index of the current unit
    unit_index = 0

    # Divide the size by 1024 until it is less than 1024
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1

    # Format the size with 2 decimal places and the appropriate unit
    return f"{size:.2f} {units[unit_index]}"


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
    Get the type of filesystem at the given path.

    Args:
        path (str | Path): The path to get the filesystem type for.

    Returns:
        str | None: The type of filesystem at the path, or None if the path is invalid.
    """

    # Convert path to Path object
    path = Path(path).resolve()

    # Find the partition that the path is on, based on the mountpoint
    best_part = max(
        (part for part in disk_partitions(all=True) if path.as_posix().startswith(part.mountpoint)),
        key=lambda part: len(part.mountpoint),
        default=None,
    )

    # Return the filesystem type of the partition
    return best_part.fstype if best_part else None


def has_available_space(path: str | PathLike, required_size: int, minimum_space: int = 1) -> bool:
    """
    Check if there is sufficient space available at the specified path.

    Args:
        path (str | PathLike): The file or directory path to check for available space.
        required_size (int): The size of the file or data to be stored, in bytes.
        minimum_space (int): The minimum additional space to ensure, in gigabytes. Defaults to 1.

    Returns:
        bool: True if there is enough available space, False otherwise.
    """

    # Convert path to Path object
    path = Path(path)

    # Calculate the total required space including the minimum space buffer
    required_space = required_size + (minimum_space * 1024 * 1024 * 1024)

    # Get the disk usage statistics for the appropriate path (parent if it's a file or doesn't exist)
    disk_usage_obj = disk_usage(path.parent.as_posix() if path.is_file() or not path.exists() else path.as_posix())

    # Return True if there is enough free space, False otherwise
    return bool(disk_usage_obj.free >= required_space)


def looks_like_a_ram_directory(path: str | Path) -> bool:
    """
    Check if a path is a temporary RAM-backed filesystem.

    Args:
        path (str | Path): The path to check.

    Returns:
        bool: True if the path is a temporary RAM-backed filesystem, False otherwise.
    """

    # List of known RAM-backed filesystems
    ram_filesystems = {"tmpfs", "ramfs", "devtmpfs"}

    # Get the filesystem type of the path
    filesystem_type = get_filesystem_type(path)

    # Check if the filesystem type is a known RAM-backed filesystem
    return filesystem_type in ram_filesystems
