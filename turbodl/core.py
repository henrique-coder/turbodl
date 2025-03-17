# Standard modules
from os import PathLike
from pathlib import Path
from signal import SIGINT, SIGTERM, Signals, signal
from sys import exit
from types import FrameType
from typing import Literal, NoReturn

# Third-party modules
from httpx import Client, Limits, Timeout
from humanfriendly import format_size
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

# Local imports
from .buffers import ChunkBuffer
from .downloaders import download_with_buffer, download_without_buffer
from .exceptions import DownloadInterruptedError, InvalidArgumentError, NotEnoughSpaceError, UnidentifiedFileSizeError
from .utils import (
    CustomDownloadColumn,
    CustomSpeedColumn,
    CustomTimeColumn,
    bool_to_yes_no,
    calculate_max_connections,
    fetch_file_info,
    generate_chunk_ranges,
    has_available_space,
    is_ram_directory,
    truncate_url,
    validate_headers,
    verify_hash,
)


class TurboDL:
    def __init__(
        self, max_connections: int | Literal["auto"] = "auto", connection_speed_mbps: float = 100, show_progress_bar: bool = True
    ) -> None:
        """
        Initialize a TurboDL instance with specified settings.

        Args:
            max_connections (int | Literal['auto']): Maximum connections for downloading. Maximum value is 32. Defaults to 'auto'.
            connection_speed_mbps (float): Connection speed in Mbps for optimal performance. Defaults to 100.
            show_progress_bar (bool): Flag to display the progress bar. Defaults to True.
        """

        # Setup signal handlers for clean exit
        self._setup_signal_handlers()

        # Validate max_connections argument
        if isinstance(max_connections, int) and not 1 <= max_connections <= 32:
            raise InvalidArgumentError("max_connections must be between 1 and 32")

        # Validate connection_speed_mbps argument
        if connection_speed_mbps <= 0:
            raise InvalidArgumentError("connection_speed_mbps must be positive")

        # Initialize private attributes
        self._max_connections: int | Literal["auto"] = max_connections
        self._connection_speed_mbps: float = connection_speed_mbps
        self._show_progress_bar: bool = show_progress_bar
        self._output_path: Path | None = None
        self._console: Console = Console()
        self._http_client: Client = Client(
            follow_redirects=True,
            limits=Limits(max_connections=32, max_keepalive_connections=32, keepalive_expiry=60),
            verify=False,
        )
        self._chunk_buffers: dict[str, ChunkBuffer] = {}

        # Initialize public attributes
        self.output_path: str | None = None

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for clean exit on SIGINT (Ctrl+C) and SIGTERM. This is useful for cleaning up temporary files and closing the HTTP client."""

        # Setup signal handlers for clean exit
        for sig in (SIGINT, SIGTERM):
            # Set the signal handler
            signal(sig, self._signal_handler)

    def _signal_handler(self, signum: Signals, frame: FrameType | None) -> NoReturn:
        """
        Handle received signals for a clean exit.

        This method is called when the process receives a termination signal (e.g., SIGINT or SIGTERM). It ensures that necessary cleanup is performed before exiting the application.

        Args:
            signum (Signals): The signal number received.
            frame (FrameType | None): The current stack frame.
        """

        # Perform cleanup operations
        self._cleanup()

        # Exit the application with a status code of 0
        exit(0)

    def _cleanup(self) -> None:
        """
        Perform cleanup operations before exiting the application.

        This method is called when the process receives a termination signal (e.g., SIGINT or SIGTERM) or when the application completes execution. It ensures that necessary cleanup is performed, such as deleting temporary files and closing the HTTP client.
        """

        # Remove temporary files if they exist
        if isinstance(self._output_path, Path):
            self._output_path.unlink(missing_ok=True)

        # Close the HTTP client to free up system resources
        if hasattr(self, "_http_client"):
            self._http_client.close()

    def download(
        self,
        url: str,
        output_path: str | PathLike | None = None,
        pre_allocate_space: bool = False,
        enable_ram_buffer: bool | Literal["auto"] = "auto",
        overwrite: bool = True,
        headers: dict[str, str] | None = None,
        inactivity_timeout: int | None = 120,
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
        """Download a file from the given URL to the specified output path.

        Args:
            url (str): The URL of the file to download.
            output_path (str | PathLike | None): The path to save the downloaded file. If it is a directory, filename is derived from server response. If None, the current working directory is used. Defaults to None.
            pre_allocate_space (bool): Whether to pre-allocate disk space for the file. Defaults to False.
            enable_ram_buffer (bool | Literal["auto"]): Use RAM buffer for download. If set to False, the file will be downloaded continuously to disk. If set to True, the file will be downloaded with the help of RAM memory. If set to "auto", the RAM buffer will be disabled if the output path is a RAM directory and enabled otherwise. Defaults to "auto".
            overwrite (bool): Overwrite existing file if true. Defaults to True.
            headers (dict[str, str] | None): Additional headers for the request. Defaults to None.
            inactivity_timeout (int | None): Timeout in seconds after no data is received. None means no timeout. Defaults to 120.
            timeout (int | None): Total timeout for the download request. Defaults to None.
            expected_hash (str | None): Expected hash for file verification. Defaults to None.
            hash_type (Literal): Hash algorithm to use for verification. Available: md5, sha1, sha224, sha256, sha384, sha512, blake2b, blake2s, sha3_224, sha3_256, sha3_384, sha3_512, shake_128, shake_256. Defaults to "md5".

        Raises:
            NotEnoughSpaceError: If there's not enough space to download the file.
            DownloadInterruptedError: If the download is interrupted by the user.
        """

        # Validate and set headers and timeout
        self._http_client.headers.update(validate_headers(headers))

        # Configure timeout settings
        custom_timeout = None

        if timeout is not None or inactivity_timeout is not None:
            custom_timeout = Timeout(connect=30, read=inactivity_timeout, write=inactivity_timeout, pool=timeout)

        self._http_client.timeout = custom_timeout

        # Set and resolve the output path
        self._output_path = Path.cwd() if output_path is None else Path(output_path).resolve()

        # Determine if output path is a RAM directory and set RAM buffer flag
        is_ram_dir = is_ram_directory(self._output_path)

        if enable_ram_buffer == "auto":
            enable_ram_buffer = not is_ram_dir

        # Fetch file information from the server
        remote_file_info = fetch_file_info(self._http_client, url)

        # Extract and log file details
        url: str = remote_file_info.url
        filename: str = remote_file_info.filename
        size: int | Literal["unknown"] = remote_file_info.size

        if size == "unknown":
            raise UnidentifiedFileSizeError(
                "Unable to detect file size. Support for files without a fixed size is under development."
            )

        # Calculate optimal connections and chunk ranges
        if self._max_connections == "auto":
            self._max_connections = calculate_max_connections(size, self._connection_speed_mbps)

        chunk_ranges = generate_chunk_ranges(size, self._max_connections)

        # Check for available disk space
        if not has_available_space(self._output_path, size):
            raise NotEnoughSpaceError(f"Not enough space to download {filename}")

        # Append filename if output path is a directory
        if self._output_path.is_dir():
            self._output_path = Path(self._output_path, filename)

        # Handle existing files based on the overwrite flag
        if not overwrite:
            base_name = self._output_path.stem
            extension = self._output_path.suffix
            counter = 1

            while self._output_path.exists():
                self._output_path = Path(self._output_path.parent, f"{base_name}_{counter}{extension}")
                counter += 1

        try:
            # Pre-allocate space if required
            if pre_allocate_space:
                with Progress(
                    SpinnerColumn(spinner_name="dots", style="bold cyan"),
                    TextColumn(f"[bold cyan]Pre-allocating space for {size} bytes...", justify="left"),
                    transient=True,
                    disable=not self._show_progress_bar,
                ) as progress:
                    progress.add_task("", total=None)

                with self._output_path.open("wb") as fo:
                    fo.truncate(size)
            else:
                self._output_path.touch(exist_ok=True)

            # Display progress bar header
            if self._show_progress_bar:
                self._console.print(
                    f"[bold bright_black]╭ [green]Downloading [blue]{truncate_url(url)} [bright_black]• [green]{'~' + format_size(size) if size is not None else 'Unknown'}"
                )
                self._console.print(
                    f"[bold bright_black]│ [green]Output file: [cyan]{self._output_path.as_posix()} [bright_black]• [green]RAM buffer: [cyan]{bool_to_yes_no(enable_ram_buffer)} [bright_black]• [green]Connections: [cyan]{self._max_connections}"
                )

            # Setup progress bar and execute download
            with Progress(
                *[
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
                ],
                disable=not self._show_progress_bar,
            ) as progress:
                task_id = progress.add_task("download", total=size, filename=self._output_path.name)

                if enable_ram_buffer:
                    download_with_buffer(
                        self._http_client, url, self._output_path, size, self._chunk_buffers, chunk_ranges, task_id, progress
                    )
                else:
                    download_without_buffer(self._http_client, url, self._output_path, chunk_ranges, task_id, progress)
        except KeyboardInterrupt as e:
            self._cleanup()  # Clean up after interruption
            raise DownloadInterruptedError("Download interrupted by user") from e
        except Exception as e:
            self._cleanup()  # Clean up after failure
            raise e

        # Set the output path attribute
        self.output_path = self._output_path.as_posix()

        # Verify the hash of the downloaded file, if provided
        if expected_hash is not None:
            verify_hash(self._output_path, expected_hash, hash_type)
