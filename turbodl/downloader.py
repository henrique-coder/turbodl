# Built-in imports
from concurrent.futures import ThreadPoolExecutor
from hashlib import new as hashlib_new
from io import BytesIO
from math import ceil, log2, sqrt
from mimetypes import guess_extension as guess_mimetype_extension
from mmap import ACCESS_WRITE, mmap
from os import PathLike, ftruncate
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from urllib.parse import unquote, urlparse

# Third-party imports
from httpx import Client, HTTPError, HTTPStatusError, Limits, RemoteProtocolError
from psutil import disk_usage, virtual_memory
from rich.progress import BarColumn, DownloadColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from tenacity import retry, stop_after_attempt, wait_exponential

# Local imports
from .exceptions import DownloadError, HashVerificationError, InsufficientSpaceError, RequestError


class ChunkBuffer:
    """
    A class for buffering chunks of data.
    """

    def __init__(self, chunk_size_mb: int = 256, max_buffer_mb: int = 1024) -> None:
        """
        Initialize the ChunkBuffer class.

        Args:
            chunk_size_mb: The size of each chunk in megabytes.
            max_buffer_mb: The maximum size of the buffer in megabytes.
        """

        self.chunk_size = chunk_size_mb * 1024 * 1024
        self.max_buffer_size = min(max_buffer_mb * 1024 * 1024, virtual_memory().available * 0.30)
        self.current_buffer = BytesIO()
        self.current_size = 0
        self.total_buffered = 0

    def write(self, data: bytes, total_file_size: int) -> Optional[bytes]:
        """
        Write data to the buffer.

        Args:
            data: The data to write to the buffer.
            total_file_size: The total size of the file in bytes.

        Returns:
            The chunk data if the buffer is full, None otherwise.
        """

        self.current_buffer.write(data)
        self.current_size += len(data)
        self.total_buffered += len(data)

        if (
            self.current_size >= self.chunk_size
            or self.total_buffered >= total_file_size
            or self.current_size >= self.max_buffer_size
        ):
            chunk_data = self.current_buffer.getvalue()

            self.current_buffer.close()
            self.current_buffer = BytesIO()
            self.current_size = 0

            return chunk_data

        return None


class TurboDL:
    """
    A class for downloading direct download URLs.
    """

    def __init__(
        self,
        max_connections: Union[int, Literal["auto"]] = "auto",
        connection_speed: float = 80,
        overwrite: bool = True,
        show_progress_bars: bool = True,
        custom_headers: Optional[Dict[Any, Any]] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Initialize the class with the required settings for downloading a file.

        Args:
            max_connections: The maximum number of connections to use for downloading the file. (default: "auto")
            connection_speed: Your connection speed in Mbps (megabits per second). (default: 80)
            overwrite: Overwrite the file if it already exists. Otherwise, a "_1", "_2", etc. suffix will be added. (default: True)
            show_progress_bars: Show or hide all progress bars. (default: True)
            custom_headers: Custom headers to include in the request. If None, default headers will be used. Imutable headers are "Accept-Encoding", "Connection" and "Range". (default: None)
            timeout: Timeout in seconds for the download process. Or None for no timeout. (default: None)

        Raises:
            ValueError: If max_connections is not between 1 and 32 or connection_speed is not positive.
        """

        self._max_connections: Union[int, Literal["auto"]] = max_connections
        self._connection_speed: int = connection_speed

        if isinstance(self._max_connections, int):
            if not 1 <= self._max_connections <= 32:
                raise ValueError("max_connections must be between 1 and 32")

        if self._connection_speed <= 0:
            raise ValueError("connection_speed must be positive")

        self._overwrite: bool = overwrite
        self._show_progress_bars: bool = show_progress_bars
        self._timeout: Optional[int] = timeout

        self._custom_headers: Dict[Any, Any] = {
            "Accept": "*/*",
            "Accept-Encoding": "identity",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        if custom_headers:
            for key, value in custom_headers.items():
                if key.title() not in ["Accept-Encoding", "Range", "Connection"]:
                    self._custom_headers[key.title()] = value

        self._client: Client = Client(
            headers=self._custom_headers,
            follow_redirects=True,
            verify=True,
            limits=Limits(max_keepalive_connections=32, max_connections=64),
            timeout=self._timeout,
        )

        self.output_path: str = None

    def _is_enough_space_to_download(self, path: Union[str, PathLike], size: int) -> bool:
        """
        Checks if there is enough space to download the file.

        Args:
            path: The path to save the downloaded file to.
            size: The size of the file in bytes.

        Returns:
            True if there is enough space, False otherwise.
        """

        path = Path(path)

        required_space = size + (1 * 1024 * 1024 * 1024)
        disk_usage_obj = disk_usage(path.parent.as_posix() if path.is_file() or not path.exists() else path.as_posix())

        if disk_usage_obj.free < required_space:
            return False

        return True

    def _calculate_connections(self, file_size: int, connection_speed: Union[float, Literal["auto"]]) -> int:
        """
        Calculates the optimal number of connections based on file size and connection speed.

        Uses a sophisticated formula that considers:
        - File size scaling using logarithmic growth
        - Connection speed with square root scaling
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
            file_size: The size of the file in bytes.
            connection_speed: Your connection speed in Mbps.

        Returns:
            Estimated optimal number of connections, capped between 2 and 24.
        """

        if self._max_connections != "auto":
            return self._max_connections

        file_size_mb = file_size / (1024 * 1024)
        speed = 80.0 if connection_speed == "auto" else float(connection_speed)

        beta = 5.6
        base_size = 1.0
        conn_float = beta * log2(1 + file_size_mb / base_size) * sqrt(speed / 100)

        return max(2, min(24, ceil(conn_float)))

    def _get_chunk_ranges(self, total_size: int) -> List[Tuple[int, int]]:
        """
        Calculate the optimal chunk ranges for downloading a file.

        Args:
            total_size: The total size of the file in bytes.

        Returns:
            A list of tuples containing the start and end indices of each chunk.
        """

        if total_size == 0:
            return [(0, 0)]

        connections = self._calculate_connections(total_size, self._connection_speed)
        chunk_size = ceil(total_size / connections)

        ranges = []
        start = 0

        while total_size > 0:
            current_chunk = min(chunk_size, total_size)
            end = start + current_chunk - 1
            ranges.append((start, end))
            start = end + 1
            total_size -= current_chunk

        return ranges

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=5), reraise=True)
    def _get_file_info(self, url: str) -> Tuple[Optional[int], Optional[str], Optional[str]]:
        """
        Get information about the file to be downloaded.

        Args:
            url: The URL of the file to be downloaded.

        Returns:
            A tuple containing the file size in bytes, mimetype, and filename. If the information cannot be retrieved, returns None.
        """

        try:
            r = self._client.head(url, headers=self._custom_headers, timeout=self._timeout)
        except RemoteProtocolError:
            return (None, None, None)
        except HTTPError as e:
            raise RequestError(f"An error occurred while getting file info: {str(e)}") from e

        headers = r.headers

        content_length = int(headers.get("content-length", 0))
        content_type = headers.get("content-type", "application/octet-stream").split(";")[0].strip()

        if content_disposition := headers.get("content-disposition"):
            if "filename*=" in content_disposition:
                filename = content_disposition.split("filename*=")[-1].split("'")[-1]
            elif "filename=" in content_disposition:
                filename = content_disposition.split("filename=")[-1].strip("\"'")
            else:
                filename = None
        else:
            filename = None

        if not filename:
            filename = Path(unquote(urlparse(url).path)).name or f"file{guess_mimetype_extension(content_type) or ''}"

        return (content_length, content_type, filename)

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=1, max=10), reraise=True)
    def _download_chunk(self, url: str, start: int, end: int, progress: Progress, task_id: int) -> bytes:
        """
        Download a chunk of a file from the provided URL.

        Args:
            url: The URL of the file to be downloaded.
            start: The start index of the chunk.
            end: The end index of the chunk.
            progress: The progress bar to update.
            task_id: The task ID of the progress bar.

        Returns:
            The downloaded chunk as bytes.
        """

        headers = {**self._custom_headers}

        if end > 0:
            headers["Range"] = f"bytes={start}-{end}"

        try:
            with self._client.stream("GET", url, headers=headers) as r:
                r.raise_for_status()

                chunk = b""

                for data in r.iter_bytes(chunk_size=8192):
                    chunk += data
                    progress.update(task_id, advance=len(data))

                return chunk
        except HTTPStatusError as e:
            raise DownloadError(f"An error occurred while downloading chunk: {str(e)}") from e

    def _download_with_buffer(
        self, url: str, output_path: Union[str, PathLike], total_size: int, progress: Progress, task_id: int
    ) -> None:
        """
        Download a file from the provided URL to the output file path using a buffer.

        Args:
            url: The URL of the file to be downloaded.
            output_path: The path to save the downloaded file to.
            total_size: The total size of the file in bytes.
            progress: The progress bar to update.
            task_id: The task ID of the progress bar.
        """

        chunk_buffers = {}
        write_positions = {}

        def download_worker(start: int, end: int, chunk_id: int) -> None:
            """
            Download a chunk of a file from the provided URL.

            Args:
                start: The start index of the chunk.
                end: The end index of the chunk.
                chunk_id: The ID of the chunk.
            """

            chunk_buffers[chunk_id] = ChunkBuffer()
            headers = {**self._custom_headers}

            if end > 0:
                headers["Range"] = f"bytes={start}-{end}"

            try:
                with self._client.stream("GET", url, headers=headers) as r:
                    r.raise_for_status()

                    for data in r.iter_bytes(chunk_size=1024 * 1024):
                        if complete_chunk := chunk_buffers[chunk_id].write(data, total_size):
                            write_to_file(complete_chunk, start + write_positions[chunk_id])
                            write_positions[chunk_id] += len(complete_chunk)

                        progress.update(task_id, advance=len(data))

                    if remaining := chunk_buffers[chunk_id].current_buffer.getvalue():
                        write_to_file(remaining, start + write_positions[chunk_id])
            except Exception as e:
                raise DownloadError(f"Download error: {str(e)}")

        def write_to_file(data: bytes, position: int) -> None:
            """
            Write data to the output file at the specified position.

            Args:
                data: The data to write to the file.
                position: The position in the file to write the data.
            """

            with Path(output_path).open("r+b") as f:
                current_size = f.seek(0, 2)

                if current_size < total_size:
                    ftruncate(f.fileno(), total_size)

                with mmap(f.fileno(), length=total_size, access=ACCESS_WRITE) as mm:
                    mm[position : position + len(data)] = data
                    mm.flush()

        ranges = self._get_chunk_ranges(total_size)

        for i, (_, _) in enumerate(ranges):
            write_positions[i] = 0

        with ThreadPoolExecutor(max_workers=len(ranges)) as executor:
            for future in [executor.submit(download_worker, start, end, i) for i, (start, end) in enumerate(ranges)]:
                future.result()

    def _download_direct(
        self, url: str, output_path: Union[str, PathLike], total_size: int, progress: Progress, task_id: int
    ) -> None:
        """
        Download a file from the provided URL directly to the output file path.

        Args:
            url: The URL of the file to be downloaded.
            output_path: The path to save the downloaded file to.
            total_size: The total size of the file in bytes.
            progress: The progress bar to update.
            task_id: The task ID of the progress bar.
        """

        write_lock = Lock()
        futures = []

        def download_worker(start: int, end: int) -> None:
            headers = {**self._custom_headers}
            if end > 0:
                headers["Range"] = f"bytes={start}-{end}"

            try:
                with self._client.stream("GET", url, headers=headers) as r:
                    r.raise_for_status()

                    with write_lock:
                        with Path(output_path).open("r+b") as fo:
                            fo.seek(start)

                            for data in r.iter_bytes(chunk_size=8192):
                                fo.write(data)
                                progress.update(task_id, advance=len(data))
            except Exception as e:
                raise DownloadError(f"An error occurred while downloading chunk: {str(e)}") from e

        ranges = self._get_chunk_ranges(total_size)

        with ThreadPoolExecutor(max_workers=len(ranges)) as executor:
            futures = [executor.submit(download_worker, start, end) for start, end in ranges]

            for future in futures:
                future.result()

    def download(
        self,
        url: str,
        output_path: Union[str, PathLike] = Path.cwd(),
        pre_allocate_space: bool = False,
        use_ram_buffer: bool = True,
        expected_hash: Optional[str] = None,
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

        - If the output_path is a directory, the file name will be generated from the server response.
        - If the output_path is a file, the file will be saved with the provided name.
        - If not provided, the file will be saved to the current working directory.

        Args:
            url: The download URL to download the file from. (required)
            output_path: The path to save the downloaded file to. If the path is a directory, the file name will be generated from the server response. If the path is a file, the file will be saved with the provided name. If not provided, the file will be saved to the current working directory. (default: Path.cwd())
            pre_allocate_space: Whether to pre-allocate space for the file, useful to avoid disk fragmentation. (default: False)
            use_ram_buffer: Whether to use a RAM buffer to download the file. (default: True)
            expected_hash: The expected hash of the downloaded file. If not provided, the hash will not be checked. (default: None)
            hash_type: The hash type to use for the hash verification. (default: "md5")

        Raises:
            DownloadError: If an error occurs while downloading the file.
            HashVerificationError: If the hash of the downloaded file does not match the expected hash.
            InsufficientSpaceError: If there is not enough space to download the file.
            RequestError: If an error occurs while getting file info.
        """

        output_path = Path(output_path).resolve()

        total_size, mimetype, suggested_filename = self._get_file_info(url)

        if (total_size, mimetype, suggested_filename) == (None, None, None):
            has_unknown_size = True
            total_size = 0
            mimetype = "application/octet-stream"
            suggested_filename = "file"
        else:
            has_unknown_size = False

        if not has_unknown_size:
            if not self._is_enough_space_to_download(output_path, total_size):
                raise InsufficientSpaceError(f'Not enough space to download {total_size} bytes to "{output_path.as_posix()}"')

        try:
            if output_path.is_dir():
                output_path = Path(output_path, suggested_filename)

            if not self._overwrite:
                base_name = output_path.stem
                extension = output_path.suffix
                counter = 1

                while output_path.exists():
                    output_path = Path(output_path.parent, f"{base_name}_{counter}{extension}")
                    counter += 1

            if not has_unknown_size:
                if pre_allocate_space and total_size > 0:
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
                else:
                    output_path.touch(exist_ok=True)
            else:
                output_path.touch(exist_ok=True)

            self.output_path = output_path.as_posix()

            progress_columns = [
                TextColumn(f'Downloading "{suggested_filename}"', style="bold magenta"),
                BarColumn(style="bold white", complete_style="bold red", finished_style="bold green"),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                TextColumn("[bold][progress.percentage]{task.percentage:>3.0f}%"),
            ]

            with Progress(*progress_columns, disable=not self._show_progress_bars) as progress:
                task_id = progress.add_task("download", total=total_size or None, filename=output_path.name)

                if total_size == 0:
                    Path(output_path).write_bytes(self._download_chunk(url, 0, 0, progress, task_id))
                else:
                    if use_ram_buffer:
                        self._download_with_buffer(url, output_path, total_size, progress, task_id)
                    else:
                        self._download_direct(url, output_path, total_size, progress, task_id)
        except KeyboardInterrupt:
            Path(output_path).unlink(missing_ok=True)
            self.output_path = None
            return None
        except Exception as e:
            raise DownloadError(f"An error occurred while downloading file: {str(e)}") from e

        if expected_hash is not None:
            hasher = hashlib_new(hash_type)

            with Path(output_path).open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hasher.update(chunk)

            file_hash = hasher.hexdigest()

            if file_hash != expected_hash:
                Path(output_path).unlink(missing_ok=True)
                self.output_path = None

                raise HashVerificationError(
                    f'Hash verification failed. Hash type: "{hash_type}". Actual hash: "{file_hash}". Expected hash: "{expected_hash}".'
                )
