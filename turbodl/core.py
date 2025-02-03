# Standard modules
from os import PathLike
from pathlib import Path
from typing import Literal

# Third-party modules
from httpx import Client, Limits
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

# Local imports
from .buffers import ChunkBuffer
from .downloaders import download_with_buffer, download_without_buffer
from .exceptions import InvalidArgumentError, NotEnoughSpaceError
from .loggers import FileLogger
from .utils import (
    CustomDownloadColumn,
    CustomSpeedColumn,
    CustomTimeColumn,
    bool_to_yes_no,
    calculate_max_connections,
    fetch_file_info,
    format_size,
    generate_chunk_ranges,
    has_available_space,
    is_ram_directory,
    validate_headers,
    verify_hash,
)


class TurboDL:
    def __init__(
        self,
        max_connections: int | Literal["auto"] = "auto",
        connection_speed_mbps: float = 80.0,
        show_progress_bar: bool = True,
        save_log_file: bool = False,
    ) -> None:
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
        self._save_log_file: bool = save_log_file
        self._logger: FileLogger | None = None
        self._console: Console = Console()
        self._http_client: Client = Client(
            follow_redirects=True,
            limits=Limits(max_connections=64, max_keepalive_connections=32, keepalive_expiry=10),
            timeout=None,
        )
        self._chunk_buffers: dict[str, ChunkBuffer] = {}

        # Initialize public attributes
        self.output_path: str | None = None

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
        # Validate arguments
        self._http_client.headers.update(validate_headers(headers))
        self._http_client.timeout = timeout

        # Set the output path
        self._output_path = Path.cwd() if output_path is None else Path(output_path).resolve()

        # Determine if the output path is a RAM directory and set the enable_ram_buffer argument accordingly
        is_ram_dir = is_ram_directory(self._output_path)

        if enable_ram_buffer == "auto":
            enable_ram_buffer = not is_ram_dir

        # Fetch file info
        remote_file_info = fetch_file_info(self._http_client, url)
        url: str = remote_file_info.url
        filename: str = remote_file_info.filename
        size: int = remote_file_info.size

        # Calculate the number of connections to use for the download
        if self._max_connections == "auto":
            self._max_connections = calculate_max_connections(size, self._connection_speed_mbps)

        # Calculate the optimal chunk ranges
        chunk_ranges = generate_chunk_ranges(size, self._max_connections)

        # Check if there is enough space to download the file
        if not has_available_space(self._output_path, size):
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

            # Set up logger
            if self._save_log_file:
                self._logger = FileLogger(Path(self._output_path.parent, "turbodl-download.log"), overwrite=False)

            # Set the output path
            self.output_path = self._output_path.as_posix()

            # Set up progress bar header text
            if self._show_progress_bar:
                self._console.print(
                    f"[bold bright_black]╭ [green]Downloading [blue]{url} [bright_black]• [green]{'~' + format_size(size) if size is not None else 'Unknown'}"
                )
                self._console.print(
                    f"[bold bright_black]│ [green]Output file: [cyan]{self.output_path} [bright_black]• [green]RAM dir: [cyan]{bool_to_yes_no(is_ram_dir)} [bright_black]• [green]RAM buffer: [cyan]{bool_to_yes_no(enable_ram_buffer)} [bright_black]• [green]Connection speed: [cyan]{self._connection_speed_mbps} Mbps"
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
                        self._http_client, url, self._output_path, size, self._chunk_buffers, chunk_ranges, task_id, progress
                    )
                else:
                    download_without_buffer(self._http_client, url, self._output_path, chunk_ranges, task_id, progress)
        except KeyboardInterrupt:
            # Handle download interruption by user
            self._output_path.unlink(missing_ok=True)
            self._output_path = None
            self.output_path = None

        # Check the hash of the downloaded file
        if expected_hash is not None:
            verify_hash(self._output_path, expected_hash, hash_type)
