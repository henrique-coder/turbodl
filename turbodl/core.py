# Standard modules
from os import PathLike
from pathlib import Path
from signal import SIGINT, SIGTERM, Signals, signal
from sys import exit
from tempfile import gettempdir
from types import FrameType
from typing import Literal, NoReturn

# Third-party modules
from httpx import Client, Limits
from humanfriendly import format_size
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

# Local imports
from .buffers import ChunkBuffer
from .downloaders import download_with_buffer, download_without_buffer
from .exceptions import DownloadInterruptedError, InvalidArgumentError, NotEnoughSpaceError
from .loggers import LogToFile
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
    validate_headers,
    verify_hash,
)


class TurboDL:
    def __init__(
        self, max_connections: int | Literal["auto"] = "auto", connection_speed_mbps: float = 80.0, show_progress_bar: bool = True
    ) -> None:
        # Setup signal handlers
        self._setup_signal_handlers()

        # Validate arguments
        if isinstance(max_connections, int) and not 1 <= max_connections <= 32:
            raise InvalidArgumentError("max_connections must be between 1 and 32")

        if connection_speed_mbps <= 0:
            raise InvalidArgumentError("connection_speed_mbps must be positive")

        # Initialize private attributes
        self._max_connections: int | Literal["auto"] = max_connections
        self._connection_speed_mbps: float = connection_speed_mbps
        self._show_progress_bar: bool = show_progress_bar
        self._output_path: Path | None = None
        self._logger: LogToFile = LogToFile(log_file_path=Path(gettempdir(), "turbodl.log"), overwrite=False)
        self._console: Console = Console()
        self._http_client: Client = Client(
            follow_redirects=True,
            limits=Limits(max_connections=32, max_keepalive_connections=32, keepalive_expiry=30),
            timeout=None,
        )
        self._chunk_buffers: dict[str, ChunkBuffer] = {}

        # Initialize public attributes
        self.output_path: str | None = None

    def _setup_signal_handlers(self) -> None:
        for sig in (SIGINT, SIGTERM):
            signal(sig, self._signal_handler)

    def _signal_handler(self, signum: Signals, frame: FrameType | None) -> NoReturn:
        self._cleanup()

        exit(0)

    def _cleanup(self) -> None:
        if isinstance(self._output_path, Path):
            self._output_path.unlink(missing_ok=True)

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
        self._logger.info(f"Starting download of {url}")

        # Validate arguments
        self._http_client.headers.update(validate_headers(headers))
        self._http_client.timeout = timeout

        # Set the output path
        self._output_path = Path.cwd() if output_path is None else Path(output_path).resolve()
        self._logger.debug(f"Output path: {self._output_path}")

        # Determine if the output path is a RAM directory and set the enable_ram_buffer argument accordingly
        is_ram_dir = is_ram_directory(self._output_path)

        self._logger.debug(f"Is RAM directory: {is_ram_dir} ({bool_to_yes_no(is_ram_dir)})")

        if enable_ram_buffer == "auto":
            enable_ram_buffer = not is_ram_dir

        self._logger.debug(f"Enable RAM buffer: {enable_ram_buffer} ({bool_to_yes_no(enable_ram_buffer)})")

        # Fetch file info
        try:
            remote_file_info = fetch_file_info(self._http_client, url)
        except Exception as e:
            self._logger.error(f"Error fetching file info: {e}")

            raise e

        url: str = remote_file_info.url
        filename: str = remote_file_info.filename + ".turbodownload"
        mimetype: str = remote_file_info.mimetype
        size: int = remote_file_info.size

        self._logger.debug(f"URL: {url}")
        self._logger.debug(f"Filename: {filename}")
        self._logger.debug(f"Mimetype: {mimetype}")
        self._logger.debug(f"Size: {size} ({format_size(size)})")

        # Calculate the number of connections to use for the download
        if self._max_connections == "auto":
            self._max_connections = calculate_max_connections(size, self._connection_speed_mbps)

        self._logger.debug(f"Max connections: {self._max_connections}")

        # Calculate the optimal chunk ranges
        chunk_ranges = generate_chunk_ranges(size, self._max_connections)

        self._logger.debug(f"Chunk ranges: {chunk_ranges} ({len(chunk_ranges)} chunk(s))")

        # Check if there is enough space to download the file
        if not has_available_space(self._output_path, size):
            self._logger.error(f"Not enough space to download {filename}")
            raise NotEnoughSpaceError(f"Not enough space to download {filename}")

        # If output path is a directory, append filename
        if self._output_path.is_dir():
            self._output_path = Path(self._output_path, filename)

        # Handle the case where output file already exists
        if not overwrite:
            base_name = self._output_path.stem
            extension = self._output_path.suffix
            counter = 1

            while self._output_path.exists():
                self._output_path = Path(self._output_path.parent, f"{base_name}_{counter}{extension}")
                counter += 1

        try:
            # Handle pre-allocation of space if required
            if pre_allocate_space:
                self._logger.info(f"Pre-allocating space for {size} bytes...")

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

            self._logger.info(f"Output file (in progress): {self._output_path.as_posix()}")

            # Set up progress bar header text
            if self._show_progress_bar:
                self._console.print(
                    f"[bold bright_black]╭ [green]Downloading [blue]{url} [bright_black]• [green]{'~' + format_size(size) if size is not None else 'Unknown'}"
                )
                self._console.print(
                    f"[bold bright_black]│ [green]Output file: [cyan]{self._output_path.with_suffix('').as_posix()} (.turbodownload) [bright_black]• [green]RAM directory/buffer: [cyan]{bool_to_yes_no(is_ram_dir)}/{bool_to_yes_no(enable_ram_buffer)} [bright_black]• [green]Connections: [cyan]{self._max_connections} [bright_black]• [green]Speed: [cyan]{self._connection_speed_mbps} Mbps"
                )

            # Set up progress bar and start download
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
                        self._http_client,
                        url,
                        self._output_path,
                        size,
                        self._chunk_buffers,
                        chunk_ranges,
                        task_id,
                        progress,
                        self._logger,
                    )
                else:
                    download_without_buffer(
                        self._http_client, url, self._output_path, chunk_ranges, task_id, progress, self._logger
                    )
        except KeyboardInterrupt as e:
            self._logger.info("Download interrupted by user")

            # Handle download interruption by user
            self._cleanup()

            raise DownloadInterruptedError("Download interrupted by user") from e
        except Exception as e:
            self._logger.error(f"Download failed. Error: {e}")

            # Handle download failure
            self._cleanup()

            raise e

        # Remove the .turbodownload suffix
        self._output_path.rename(self._output_path.with_suffix(""))
        self._output_path = self._output_path.with_suffix("")

        self._logger.info(f"Download completed. Saved to: {self._output_path.as_posix()}")

        # Set the output path attribute
        self.output_path = self._output_path.as_posix()

        # Check the hash of the downloaded file
        if expected_hash is not None:
            self._logger.info("Checking hash...")

            verify_hash(self._output_path, expected_hash, hash_type)

            self._logger.info("Hash verification successful")

        self._logger.blank_line()

        return None
