# Built-in imports
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from hashlib import new as hashlib_new
from io import BytesIO
from logging import INFO, WARNING, FileHandler, Formatter, getLogger
from mmap import ACCESS_WRITE, mmap
from os import PathLike, ftruncate
from pathlib import Path
from threading import Lock
from typing import Any, Literal

# Third-party imports
from httpx import Client, ConnectError, HTTPStatusError, Limits, ReadTimeout
from psutil import virtual_memory
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
from tenacity import before_sleep_log, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

# Local imports
from .exceptions import HashVerificationError, InsufficientSpaceError, InvalidArgumentError
from .utils import (
    CustomDownloadColumn,
    CustomSpeedColumn,
    CustomTimeColumn,
    bool_to_yes_no,
    fetch_file_info,
    format_size,
    get_chunk_ranges,
    has_available_space,
    looks_like_a_ram_directory,
)


def download_retry_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    A decorator that wraps a function in a tenacity retry loop.

    The retry loop will retry the function up to 10 times with an exponential backoff
    strategy. The waiting time between retries is calculated as 2^retry_count * 1 second.
    The function will be retried if any of the following exceptions are raised:
        - httpx.HTTPStatusError
        - httpx.ConnectError
        - httpx.ReadTimeout
        - ConnectionError
        - TimeoutError
        - IOError

    The decorator will log the error using the "turbodl" logger before each retry.

    Args:
        func (Callable[..., Any]): The function to be decorated.

    Returns:
        Callable[..., Any]: The decorated function.
    """

    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=1, min=4, max=120),
        retry=retry_if_exception_type((HTTPStatusError, ConnectError, ReadTimeout, ConnectionError, TimeoutError, IOError)),
        before_sleep=before_sleep_log(getLogger("turbodl"), INFO),
        reraise=True,
    )
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """
        The wrapper function that is called by the retry decorator.

        Args:
            *args (Any): The arguments passed to the function.
            *kwargs (Any): The keyword arguments passed to the function.

        Returns:
            Any: The return value of the function.
        """

        self = args[0]

        try:
            # Call the function with the given arguments and keyword arguments
            return func(*args, **kwargs)
        except Exception as e:
            # Log the error using the "turbodl" logger
            if self._logger:
                self._logger.error(f"Error in {func.__name__}: {str(e)}")

            # Raise the exception
            raise e

    return wrapper


class ChunkBuffer:
    """
    A class for buffering chunks of data.
    """

    def __init__(self, chunk_size_bytes: int = 256 * (1024**2), max_buffer_bytes: int = 1 * (1024**3)) -> None:
        """
        Initialize the ChunkBuffer class.

        This class is used to buffer chunks of data. The buffer size is limited by the available
        virtual memory and the maximum buffer size. The chunks are written to the buffer in
        order to be able to write the data to the file in chunks.

        Args:
            chunk_size_bytes (int): The size of each chunk in bytes.
            max_buffer_bytes (int): The maximum size of the buffer in bytes.
        """

        # Calculate the chunk size in bytes
        self.chunk_size = chunk_size_bytes

        # Calculate the maximum buffer size in bytes
        # The maximum buffer size is the minimum of the maximum buffer size and 30% of the available virtual memory
        self.max_buffer_size = min(max_buffer_bytes, virtual_memory().available * 0.30)

        # Initialize the current buffer as an empty BytesIO object
        self.current_buffer = BytesIO()

        # Initialize the current size of the buffer to 0
        self.current_size = 0

        # Initialize the total amount of data buffered to 0
        self.total_buffered = 0

    def write(self, data: bytes, total_file_size_bytes: int, logger: Callable[..., Any]) -> bytes | None:
        """
        Write data to the buffer.

        The following conditions must be met before writing data to the buffer:
        - The current buffer size must be less than the maximum buffer size.
        - The total size of data written to the buffer must be less than the maximum buffer size.
        - The total size of data written to the buffer must be less than the total file size.

        Args:
            data (bytes): The data to write to the buffer.
            total_file_size_bytes (int): The total size of the file in bytes.
            logger (Callable[..., Any]): The logger function.

        Returns:
            bytes | None: Returns buffered data when buffer is full or conditions are met, None if buffer still has space.
        """

        logger("info", f"Writing to buffer: {len(data)} bytes")
        logger(
            "info",
            f"Buffer stats - Current size: {self.current_size}, Total buffered: {self.total_buffered}, Max size: {self.max_buffer_size}",
        )

        # Check if the current buffer size is less than the maximum buffer size
        if self.current_size + len(data) > self.max_buffer_size:
            self.logger("info", "Buffer would exceed max size, returning None")

            return None

        # Check if the total size of data written to the buffer is less than the maximum buffer size
        if self.total_buffered + len(data) > self.max_buffer_size:
            self.logger("info", "Total buffer would exceed max size, returning None")

            return None

        # Check if the total size of data written to the buffer is less than the total file size
        if self.total_buffered + len(data) > total_file_size_bytes:
            self.logger("info", "Total buffer would exceed total file size, returning None")

            return None

        self.current_buffer.write(data)
        self.current_size += len(data)
        self.total_buffered += len(data)

        if (
            self.current_size >= self.chunk_size
            or self.total_buffered >= total_file_size_bytes
            or self.current_size >= self.max_buffer_size
        ):
            chunk_data = self.current_buffer.getvalue()

            self.current_buffer.close()
            self.current_buffer = BytesIO()
            self.current_size = 0

            return chunk_data

        return None


class TurboDL:
    """A class for downloading direct download URLs."""

    def __init__(
        self,
        max_connections: int | str | Literal["auto"] = "auto",
        connection_speed: float = 80,
        show_progress_bars: bool = True,
        save_logfile: bool = False,
    ) -> None:
        """
        Initialize the class with the required settings for downloading a file.

        Args:
            max_connections (int | str | Literal['auto']): The maximum number of connections to use for downloading the file. Defaults to 'auto'.
                - 'auto' will dynamically calculate the number of connections based on the file size and connection speed.
                - An integer between 1 and 24 will set the number of connections to that value.
            connection_speed (float): Your connection speed in Mbps (megabits per second). Defaults to 80.
                - Your connection speed will be used to help calculate the optimal number of connections.
            show_progress_bars (bool): Show or hide all progress bars. Defaults to True.
            save_logfile (bool): Save log messages to a file. Defaults to False.

        Raises:
            InvalidArgumentError: If max_connections is not 'auto' or an integer between 1 and 32, or if connection_speed is not positive.
        """

        # Setup logging
        self._logger: Any = None
        self._setup_logging(save_logfile)

        # Initialize the console
        self._console = Console()

        # Initialize the instance variables
        self._max_connections: int | str | Literal["auto"] = max_connections
        self._connection_speed: float = connection_speed
        self._show_progress_bars: bool = show_progress_bars

        # Validate the arguments
        if isinstance(self._max_connections, str) and self._max_connections.isdigit():
            self._max_connections = int(self._max_connections)

        if not (self._max_connections == "auto" or (isinstance(self._max_connections, int) and 1 <= self._max_connections <= 24)):
            raise InvalidArgumentError(f"max_connections must be 'auto' or an integer between 1 and 24: {self._max_connections}")

        if self._connection_speed <= 0:
            raise InvalidArgumentError(f"connection_speed must be positive: {self._connection_speed}")

        # Create a client with the custom headers and settings
        self._client: Client = Client(
            verify=True,
            follow_redirects=True,
            limits=Limits(max_connections=48, max_keepalive_connections=24, keepalive_expiry=10),
        )

        # Initialize the output path to None
        self.output_path: str | None = None

    def _setup_logging(self, save_logfile: bool) -> None:
        """
        Setup logging for the TurboDL class.

        If save_logfile is True, a log file will be created with the cur ent date and time in the format "turbodl-download_<YMD_HMS>.log" in the current working directory. If save_logfile is False, no log file will be created.
        """

        # Set the logging level for the "httpx" logger to WARNING
        httpx_logger = getLogger("httpx")
        httpx_logger.setLevel(WARNING)

        if not save_logfile:
            return None

        # Create a logger and set the logging level to INFO
        self._logger = getLogger("turbodl")
        self._logger.setLevel(INFO)

        # Create a timestamp for the log file name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        log_file = Path(Path.cwd(), f"turbodl-{timestamp}.log")

        # Create a file handler and set the logging format
        file_handler = FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))

        # Add the file handler to the logger
        self._logger.addHandler(file_handler)

    def _log(self, level: str, message: str) -> None:
        """
        Log a message.

        If self._logger is not None, log the message with the specified level (info, error, warning, or debug).
        """

        if self._logger:
            # Log the message with the specified level
            if level == "info":
                self._logger.info(message)
            elif level == "error":
                self._logger.error(message)
            elif level == "warning":
                self._logger.warning(message)
            elif level == "debug":
                self._logger.debug(message)

    @download_retry_decorator
    def _download_chunk(self, url: str, start: int, end: int, progress: Progress, task_id: int, headers: dict[str, Any]) -> bytes:
        """
        Download a chunk of a file from the provided URL.

        This method sends a GET request to the provided URL with the Range header set to the start and end indices of the chunk.
        It will retry the request up to 5 times if it fails.
        """

        # Set the Range header to the start and end indices of the chunk
        if end > 0:
            headers["Range"] = f"bytes={start}-{end}"

        # Send the request and get the response
        with self._client.stream("GET", url, headers=headers) as r:
            # Raise an exception if the response status code is not 200
            r.raise_for_status()

            # Initialize the chunk as an empty bytes object
            chunk = b""

            # Iterate over the response and update the progress bar for each chunk
            for data in r.iter_bytes(chunk_size=8192):
                # Append the chunk to the result
                chunk += data

                # Update the progress bar
                progress.update(TaskID(task_id), advance=len(data))

            # Return the downloaded chunk
            return chunk

    def _download_with_buffer_file_writer(self, data: bytes, position: int, total_size: int, output_path: str | PathLike) -> None:
        """
        Write data to the output file at the specified position.
        """

        self._log("info", f"Writing buffer to file at position {position} with size {len(data)} bytes")

        # Open the file in read and write binary mode
        with Path(output_path).open("r+b") as f:
            # Get the current size of the file
            current_size = f.seek(0, 2)

            # If the file is smaller than the total size, truncate the file to the total size
            if current_size < total_size:
                self._log("info", f"Pre-allocating file from {current_size} to {total_size} bytes")

                ftruncate(f.fileno(), total_size)

            # Map the file to memory
            with mmap(f.fileno(), length=total_size, access=ACCESS_WRITE) as mm:
                # Write the data to the memory map at the specified position
                mm[position : position + len(data)] = data

                # Flush the memory map to disk
                mm.flush()

    @download_retry_decorator
    def _download_with_buffer_download_worker(
        self,
        chunk_buffers: dict[int, ChunkBuffer],
        write_positions: list[int],
        start: int,
        end: int,
        chunk_id: int,
        url: str,
        total_size: int,
        progress: Progress,
        task_id: int,
        headers: dict[str, Any],
        output_path: str | PathLike,
    ) -> None:
        """
        Download a chunk of a file from the provided URL.
        """

        self._log("info", f"Downloading chunk: {start}-{end}")

        # Initialize the chunk buffer
        chunk_buffers[chunk_id] = ChunkBuffer()

        if end > 0:
            headers["Range"] = f"bytes={start}-{end}"

        # Download the file chunk by chunk
        with self._client.stream("GET", url, headers=headers) as r:
            r.raise_for_status()

            # Iterate over the response and update the progress bar for each chunk
            for data in r.iter_bytes(chunk_size=1024 * 1024):
                # Write the chunk to the buffer
                if complete_chunk := chunk_buffers[chunk_id].write(data, total_size, self._log):
                    # Write the complete chunk to the file
                    self._download_with_buffer_file_writer(
                        complete_chunk, start + write_positions[chunk_id], total_size, output_path
                    )

                    # Update the write position
                    write_positions[chunk_id] += len(complete_chunk)

                # Update the progress bar
                progress.update(TaskID(task_id), advance=len(data))

            # Write any remaining data in the buffer to the file
            if remaining := chunk_buffers[chunk_id].current_buffer.getvalue():
                self._download_with_buffer_file_writer(remaining, start + write_positions[chunk_id], total_size, output_path)

    def _download_with_buffer(
        self, url: str, output_path: str | PathLike, total_size: int, progress: Progress, task_id: int, headers: dict[str, Any]
    ) -> None:
        """
        Download a file from the provided URL to the output file path using a buffer.

        This method downloads a file in chunks and writes each chunk to the output file as soon as it is downloaded.
        The chunks are written to the output file in order to avoid having to keep the entire file in memory.
        """

        # Get the chunk ranges
        ranges = get_chunk_ranges(total_size, self._max_connections, self._connection_speed)

        # Initialize buffers and write positions
        chunk_buffers: dict[int, ChunkBuffer] = {}
        write_positions = [0] * len(ranges)

        # Download the file
        with ThreadPoolExecutor(max_workers=len(ranges)) as executor:
            # Iterate over the chunk ranges
            for future in [
                executor.submit(
                    self._download_with_buffer_download_worker,
                    chunk_buffers,
                    write_positions,
                    start,
                    end,
                    i,
                    url,
                    total_size,
                    progress,
                    task_id,
                    headers,
                    output_path,
                )
                for i, (start, end) in enumerate(ranges)
            ]:
                future.result()

    @download_retry_decorator
    def _download_direct_download_worker(
        self,
        url: str,
        output_path: str | PathLike,
        progress: Progress,
        task_id: int,
        start: int,
        end: int,
        headers: dict[str, Any],
    ) -> None:
        """
        Download a chunk of the file and write it to the output file.

        This function is designed to be used with the ThreadPoolExecutor to download chunks concurrently.
        """

        self._log("info", f"Downloading chunk: {start}-{end}")

        # Initialize a lock for writing to the file
        write_lock = Lock()

        # Set the Range header for the request
        if end > 0:
            headers["Range"] = f"bytes={start}-{end}"

        # Stream the file chunk from the server
        with self._client.stream("GET", url, headers=headers) as r:
            # Raise an exception if the response status code is not 200
            r.raise_for_status()

            # Iterate over the response and write the chunk to the file
            for data in r.iter_bytes(chunk_size=1024 * 1024):
                chunk_len = len(data)

                # Acquire the write lock and open the output file in read-write mode
                with write_lock, Path(output_path).open("r+b") as fo:
                    # Seek to the start of the chunk and write the data
                    fo.seek(start)
                    fo.write(data)
                    start += chunk_len

                # Update the progress bar
                progress.update(TaskID(task_id), advance=chunk_len)

    def _download_direct(
        self, url: str, output_path: str | PathLike, total_size: int, progress: Progress, task_id: int, headers: dict[str, Any]
    ) -> None:
        """
        Download a file from the provided URL directly to the output file path.

        This method divides the file into chunks and downloads each chunk concurrently using multiple threads.
        The downloaded data is directly written to the specified output file path.
        """

        # List to store future objects from the ThreadPoolExecutor
        futures = []

        # Get the chunk ranges for the download
        ranges = get_chunk_ranges(total_size, self._max_connections, self._connection_speed)

        # Use ThreadPoolExecutor to download chunks concurrently
        with ThreadPoolExecutor(max_workers=len(ranges)) as executor:
            futures = [
                executor.submit(self._download_direct_download_worker, url, output_path, progress, task_id, start, end, headers)
                for start, end in ranges
            ]

            # Wait for all futures to complete
            for future in futures:
                future.result()

    def download(
        self,
        url: str,
        output_path: str | PathLike | None = None,
        pre_allocate_space: bool = False,
        use_ram_buffer: bool | Literal["auto"] = "auto",
        overwrite: bool = True,
        headers: dict[str, Any] | None = None,
        timeout: int | None = None,
        expected_hash: str | None = None,
        hash_type: Literal[
            "md5",
            "sha1",
            "sha224",
            "sha256",
            "sha384",
            "sha512",
            "blake2b",
            "blake2s",
            "sha3_224",
            "sha3_256",
            "sha3_384",
            "sha3_512",
            "shake_128",
            "shake_256",
        ] = "md5",
    ) -> None:
        """
        Downloads a file from the provided URL to the output file path.

        Args:
            url (str): The download URL to download the file from. Defaults to None.
            output_path (str | PathLike | None): The path to save the downloaded file to. If the path is a directory, the file name will be generated from the server response. If the path is a file, the file will be saved with the provided name. If not provided, the file will be saved to the current working directory. Defaults to None.
            pre_allocate_space (bool): Whether to pre-allocate space for the file, useful to avoid disk fragmentation. Defaults to False.
            use_ram_buffer (bool | str | Literal["auto"]): Whether to use a RAM buffer to download the file. If True, the file will be downloaded with the help of a RAM buffer. If False, the file will be downloaded directly to the output file path. If 'auto', the RAM buffer will be used if the output path is not a RAM directory. Defaults to 'auto'.
            overwrite (bool): Overwrite the file if it already exists. Otherwise, a '_1', '_2', etc. suffix will be added. Defaults to True.
            headers (dict[str, Any] | None): Custom headers to include in the request. If None, default headers will be used. Defaults to None.
                - Immutable headers are (case-insensitive):
                    - 'Accept-Encoding': 'identity'
                    - 'Range': ...
                    - 'Connection': ...
                - All other headers will be included in the request.
            timeout (int | None): Timeout in seconds for the download process. Or None for no timeout. Default to None.
            expected_hash (str | None): The expected hash of the downloaded file. If not provided, the hash will not be checked. Defaults to None.
            hash_type (str | Literal['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512', 'blake2b', 'blake2s', 'sha3_224', 'sha3_256', 'sha3_384', 'sha3_512', 'shake_128', 'shake_256']): The hash type to use for the hash verification. Defaults to 'md5'.

        Raises:
            InvalidArgumentError: If the URL is not provided or the use_ram_buffer is not a boolean or 'auto'.
            HashVerificationError: If the hash of the downloaded file does not match the expected hash.
            InsufficientSpaceError: If there is not enough space to download the file.
            OnlineRequestError: If an error occurs while getting file info.
        """

        self._log("info", "Starting new download:")
        self._log("info", f"Max connections: {self._max_connections}")
        self._log("info", f"Connection speed: {self._connection_speed} Mbps")
        self._log("info", f"Show progress bars: {self._show_progress_bars}")
        self._log("info", f"URL: {url}")
        self._log("info", f"Output path: {output_path}")
        self._log("info", f"Pre-allocate space: {pre_allocate_space}")
        self._log("info", f"use RAM buffer: {use_ram_buffer}")
        self._log("info", f"Overwrite: {overwrite}")
        self._log("info", f"Headers: {headers}")
        self._log("info", f"Timeout: {timeout}")
        self._log("info", f"Expected hash: {expected_hash}")
        self._log("info", f"Hash type: {hash_type}")

        # Create a dictionary with default headers and update it with custom headers
        default_headers: dict[str, Any] = {
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        }

        if headers:
            for key, value in headers.items():
                if key.title() not in {"Accept-Encoding", "Range", "Connection"}:
                    default_headers[key.title()] = value

        headers = default_headers
        self._log("info", f"Headers: {headers}")

        # Set the headers and timeout for the HTTPX client
        self._client.headers.update(headers)
        self._client.timeout = timeout

        # Check if the URL is provided
        if not url:
            message = "Missing URL value"
            self._log("error", message)

            raise InvalidArgumentError(message)

        # Resolve the output path, defaulting to the current working directory if not provided
        output_path = Path.cwd() if output_path is None else Path(output_path).resolve()
        self._log("info", f"Output path: {output_path}")

        # Check if the use_ram_buffer is a boolean or 'auto'
        if not (use_ram_buffer == "auto" or isinstance(use_ram_buffer, bool)):
            message = f"Invalid use_ram_buffer value: {use_ram_buffer}: expected 'auto' or boolean"
            self._log("error", message)

            raise InvalidArgumentError(message)

        # Determine if the output path is a RAM directory
        is_ram_directory = looks_like_a_ram_directory(output_path)
        self._log("info", f"Is RAM directory: {is_ram_directory}")

        # Determine if RAM buffer should be used (if not provided)
        if use_ram_buffer == "auto":
            use_ram_buffer = not is_ram_directory

        self._log("info", f"Use RAM buffer: {use_ram_buffer}")

        # Get the file info from the URL
        file_info = fetch_file_info(url, self._client)
        self._log("info", f"File info: {file_info}")

        # Handle the case where the file info is not available
        if file_info is None:
            has_unknown_info = True
            total_size = 0
            # mimetype = "application/octet-stream"  # TODO: Use it?
            suggested_filename = "unknown_file"
        else:
            has_unknown_info = False
            url = file_info["url"]
            total_size = int(file_info["size"])
            # mimetype = str(file_info["mimetype"])  # TODO: Use it?
            suggested_filename = str(file_info["filename"])

        self._log("info", f"URL: {url}")
        self._log("info", f"Total size: {total_size}")
        self._log("info", f"Suggested filename: {suggested_filename}")

        # Check if there is enough space to download the file
        if not has_unknown_info and not has_available_space(output_path, total_size):
            message = f"Not enough space to download {total_size} bytes to '{output_path.as_posix()}'"
            self._log("error", message)

            raise InsufficientSpaceError(message)

        try:
            # If output path is a directory, append suggested filename
            if output_path.is_dir():
                output_path = Path(output_path, suggested_filename)

            self._log("info", f"Output path: {output_path}")

            # Handle the case where output file already exists
            if not overwrite:
                base_name = output_path.stem
                extension = output_path.suffix
                counter = 1

                while output_path.exists():
                    output_path = Path(output_path.parent, f"{base_name}_{counter}{extension}")
                    counter += 1

            self._log("info", f"Output path: {output_path}")

            # Handle pre-allocation of space if requested
            if not has_unknown_info:
                if pre_allocate_space and total_size > 0:
                    self._log("info", f"Pre-allocating space for {total_size} bytes...")

                    with Progress(
                        SpinnerColumn(spinner_name="dots", style="bold cyan"),
                        TextColumn(f"[bold cyan]Pre-allocating space for {total_size} bytes...", justify="left"),
                        transient=True,
                        disable=not self._show_progress_bars,
                    ) as progress:
                        progress.add_task("", total=None)

                        if pre_allocate_space and total_size > 0:
                            with output_path.open("wb") as fo:
                                fo.truncate(total_size)

                    self._log("info", f"Successfully pre-allocated space for {total_size} bytes.")
                else:
                    output_path.touch(exist_ok=True)
            else:
                output_path.touch(exist_ok=True)

            # Set the output path
            self.output_path = output_path.as_posix()

            # Set up status message
            if self._show_progress_bars:
                self._console.print(
                    f"[bold bright_black]╭ [green]Downloading [blue]{url} [bright_black]• [green]~{format_size(total_size)}"
                )
                self._console.print(
                    f"[bold bright_black]│ [green]Output file: [cyan]{self.output_path} [bright_black]• [green]RAM dir: [cyan]{bool_to_yes_no(is_ram_directory)} [bright_black]• [green]RAM buffer: [cyan]{bool_to_yes_no(use_ram_buffer)} [bright_black]• [green]Connection speed: [cyan]{self._connection_speed} Mbps"
                )

                # Set up live progress bar
                progress_columns = [
                    TextColumn("[bold bright_black]╰─◾"),
                    BarColumn(style="bold white", complete_style="bold red", finished_style="bold green"),
                    TextColumn("[bold bright_black]•"),
                    CustomDownloadColumn(style="bold"),
                    TextColumn("[bold bright_black]• [magenta][progress.percentage]{task.percentage:>3.0f}%"),
                    TextColumn("[bold bright_black]•"),
                    CustomSpeedColumn(style="bold"),
                    TextColumn("[bold bright_black]•"),
                    CustomTimeColumn(
                        elapsed_style="bold steel_blue",
                        remaining_style="bold blue",
                        separator="•",
                        separator_style="bold bright_black",
                    ),
                ]

            # Perform the download
            with Progress(*progress_columns, disable=not self._show_progress_bars) as progress:
                task_id = progress.add_task("download", total=total_size or None, filename=output_path.name)

                # Determine download method based on buffer usage
                if total_size == 0:
                    Path(output_path).write_bytes(self._download_chunk(url, 0, 0, progress, task_id, headers))
                elif use_ram_buffer:
                    self._download_with_buffer(url, output_path, total_size, progress, task_id, headers)
                else:
                    self._download_direct(url, output_path, total_size, progress, task_id, headers)
        except KeyboardInterrupt:
            # Handle download interruption by user
            Path(output_path).unlink(missing_ok=True)
            self.output_path = None

            return None
        except Exception as e:
            self._log("error", f"Download failed: {str(e)}")

            raise e

        self._log("info", "File downloaded successfully.")

        # Verify the hash of the downloaded file if an expected hash is provided
        if expected_hash is not None:
            self._log("info", "Verifying the hash of the downloaded file...")

            # Calculate the hash of the downloaded file
            hasher = hashlib_new(hash_type)

            with Path(output_path).open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)

            file_hash = hasher.hexdigest()

            if file_hash != expected_hash:
                # Handle hash verification failure
                Path(output_path).unlink(missing_ok=True)
                self.output_path = None

                message = f'Hash verification failed. Hash type: "{hash_type}" - Actual hash: "{file_hash}" - Expected hash: "{expected_hash}"'
                self._log("error", message)

                raise HashVerificationError(message)

            self._log("info", "Hash verification successful.")
