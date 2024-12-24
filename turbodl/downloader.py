# Built-in imports
from array import array
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from hashlib import new as hashlib_new
from io import BytesIO
from math import ceil, log2, sqrt
from mimetypes import guess_extension as guess_mimetype_extension
from os import PathLike
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set, Tuple, Union
from urllib.parse import unquote, urlparse

# Third-party imports
from httpx import Client, HTTPStatusError
from psutil import virtual_memory
from rich.progress import BarColumn, DownloadColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from tenacity import retry, stop_after_attempt, wait_exponential

# Local imports
from .exceptions import DownloadError, HashVerificationError, RequestError


class TurboDL:
    """A class for downloading direct download URLs."""

    def __init__(
        self,
        max_connections: Union[int, Literal['auto']] = 'auto',
        connection_speed: float = 80,
        overwrite: bool = True,
        show_optimization_progress_bar: bool = True,
        show_progress_bar: bool = True,
        custom_headers: Optional[Dict[Any, Any]] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Initialize the class with the required settings for downloading a file.

        Args:
            max_connections: The maximum number of connections to use for downloading the file. (default: 'auto')
            connection_speed: Your connection speed in Mbps (megabits per second). (default: 80)
            overwrite: Overwrite the file if it already exists. Otherwise, a "_1", "_2", etc. suffix will be added. (default: True)
            show_optimization_progress_bar: Show or hide the initial optimization progress bar. (default: True)
            show_progress_bar: Show or hide the download progress bar. (default: True)
            custom_headers: Custom headers to include in the request. If None, default headers will be used. Imutable headers are 'Accept-Encoding' and 'Range'. (default: None)
            timeout: Timeout in seconds for the download process. Or None for no timeout. (default: None)
        """

        with Progress(
            SpinnerColumn(spinner_name='dots', style='bold cyan'),
            TextColumn('[bold cyan]Optimizing download settings...', justify='left'),
            BarColumn(bar_width=40, style='cyan', complete_style='green'),
            TimeRemainingColumn(),
            TextColumn('[bold][progress.percentage]{task.percentage:>3.0f}%'),
            transient=True,
            disable=not show_optimization_progress_bar,
        ) as progress:
            task = progress.add_task('', total=100)

            self._max_connections: Union[int, Literal['auto']] = max_connections
            self._connection_speed: int = connection_speed
            self._overwrite: bool = overwrite
            self._show_progress_bar: bool = show_progress_bar
            self._timeout: Optional[int] = timeout
            progress.update(task, advance=20)

            self._custom_headers: Dict[Any, Any] = {
                'Accept': '*/*',
                'Accept-Encoding': 'identity',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            }

            if custom_headers:
                for key, value in custom_headers.items():
                    if key.title() not in ['Accept-Encoding', 'Range']:
                        self._custom_headers[key.title()] = value

            progress.update(task, advance=20)

            self._client: Client = Client(
                headers=self._custom_headers, follow_redirects=True, verify=True, http2=True, timeout=self._timeout
            )
            progress.update(task, advance=20)

            self._buffer_size: int = min(8 * 1024 * 1024, max(1024 * 1024, self._get_optimal_buffer_size()))
            self._buffer_pool: Dict[int, memoryview] = {}
            self._active_buffers: Set[int] = set()
            progress.update(task, advance=20)

            for i in range(8):
                self._buffer_pool[i] = memoryview(array('B', [0] * self._buffer_size))

            progress.update(task, advance=20)

            self.output_path: str = None

    @lru_cache(maxsize=1)
    def _get_optimal_buffer_size(self) -> int:
        """
        Calculate the optimal buffer size based on system memory and performance factors.

        The calculation considers:
        - Available system memory
        - Minimum buffer requirements
        - Power of 2 alignment for better performance
        - Maximum practical buffer size limits

        Returns:
            Optimal buffer size in bytes aligned to system parameters
        """

        try:
            base_size = virtual_memory().available // 64
            power = max(20, min(23, (base_size - 1).bit_length()))
            optimal_size = 1 << power

            return max(1024 * 1024, min(optimal_size, 8 * 1024 * 1024))
        except Exception:
            return 1024 * 1024

    def _get_buffer(self) -> memoryview:
        """
        Get a buffer from the buffer pool.

        Returns:
            A memoryview object representing the buffer.
        """

        try:
            for i, buffer in self._buffer_pool.items():
                if i not in self._active_buffers:
                    self._active_buffers.add(i)
                    return buffer

            self._expand_buffer_pool()
            return self._get_buffer()
        except Exception:
            return memoryview(array('B', [0] * self._buffer_size))

    def _release_buffer(self, buffer: memoryview) -> None:
        """
        Release a buffer back to the buffer pool.

        Args:
            buffer: A memoryview object representing the buffer to be released.
        """

        for i, pool_buffer in self._buffer_pool.items():
            if pool_buffer == buffer:
                self._active_buffers.remove(i)
                break

    def _expand_buffer_pool(self) -> None:
        current_size = len(self._buffer_pool)
        new_size = min(current_size + 4, 32)

        for i in range(current_size, new_size):
            self._buffer_pool[i] = memoryview(array('B', [0] * self._buffer_size))

    @lru_cache(maxsize=256)
    def _calculate_connections(self, file_size: int, connection_speed: Union[float, Literal['auto']]) -> int:
        """
        Calculates the optimal number of connections based on file size and connection speed.

        Uses a sophisticated formula that considers:
        - File size scaling using logarithmic growth
        - Connection speed with square root scaling
        - System resource optimization
        - Network overhead management

        Formula:
        \[ connections = 2 \cdot \left\lceil\frac{\beta \cdot \log_2(1 + \frac{S}{M}) \cdot \sqrt{\frac{V}{100}}}{2}\right\rceil \]

        Where:
        - S: File size in MB
        - V: Connection speed in Mbps
        - M: Base size factor (1 MB)
        - β: Dynamic coefficient (5.6)

        Args:
            file_size: File size in bytes
            connection_speed: Connection speed in Mbps

        Returns:
            Even number of connections between 2 and 32
        """

        if self._max_connections != 'auto':
            return self._max_connections

        file_size_mb = file_size / (1024 * 1024)
        speed = 80.0 if connection_speed == 'auto' else float(connection_speed)

        beta = 5.6
        base_size = 1.0
        conn_float = beta * log2(1 + file_size_mb / base_size) * sqrt(speed / 100)

        return max(2, min(32, 2 * ceil(conn_float / 2)))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=5), reraise=True)
    def _get_file_info(self, url: str) -> Tuple[int, str, str]:
        """
        Retrieve file information from a given URL.

        - This method sends a HEAD request to the specified URL to obtain the file's content length, content type, and filename.
        - If the filename is not present in the 'Content-Disposition' header, it attempts to extract it from the URL path.
        - If the filename cannot be determined, a default name with the appropriate extension is generated based on the content type.

        Args:
            url: The URL of the file to retrieve information from. (required)

        Returns:
            A tuple containing the content length (int), content type (str), and filename (str).

        Raises:
            RequestError: If an error occurs while sending the HEAD request.
        """

        try:
            with self._client.stream('HEAD', url) as r:
                r.raise_for_status()
                headers = r.headers

                content_length = int(headers.get('content-length', 0))
                content_type = headers.get('content-type', 'application/octet-stream').split(';')[0].strip()

                if content_disposition := headers.get('content-disposition'):
                    if 'filename*=' in content_disposition:
                        filename = content_disposition.split('filename*=')[-1].split("'")[-1]
                    elif 'filename=' in content_disposition:
                        filename = content_disposition.split('filename=')[-1].strip('"\'')
                    else:
                        filename = None
                else:
                    filename = None

                if not filename:
                    filename = (
                        Path(unquote(urlparse(url).path)).name or f'downloaded_file{guess_mimetype_extension(content_type) or ""}'
                    )

                return (content_length, content_type, filename)
        except HTTPStatusError as e:
            raise RequestError(f'Request failed with status code "{e.response.status_code}"') from e

    @lru_cache(maxsize=256)
    def _get_chunk_ranges(self, total_size: int) -> List[Tuple[int, int]]:
        """
        Calculate and return the chunk ranges for downloading a file.

        - This method divides the total file size into smaller chunks based on the number of connections calculated.
        - Each chunk is represented as a tuple containing the start and end byte positions.

        Args:
            total_size: The total size of the file to be downloaded. (required)

        Returns:
            A list of tuples, where each tuple contains the start and end positions (in bytes) for each chunk.
            If the total size is zero, returns a single chunk with both start and end as zero.
        """

        if total_size == 0:
            return [(0, 0)]

        connections = self._calculate_connections(total_size, self._connection_speed)
        chunk_size = ceil(total_size / connections)

        ranges = []
        start = 0
        remaining = total_size

        while remaining > 0:
            current_chunk = min(chunk_size, remaining)
            end = start + current_chunk - 1
            ranges.append((start, end))
            start = end + 1
            remaining -= current_chunk

        return ranges

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True)
    def _download_chunk(self, url: str, start: int, end: int, progress: Progress, task_id: int) -> bytes:
        """
        Downloads a chunk of a file from the given URL.

        - This method sends a GET request with a 'Range' header to the specified URL to obtain the specified chunk of the file.
        - The chunk is then returned as bytes.

        Args:
            url: The URL to download the chunk from. (required)
            start: The start byte of the chunk. (required)
            end: The end byte of the chunk. (required)
            progress: The Progress object to update with the chunk's size. (required)
            task_id: The task ID to update in the Progress object. (required)

        Returns:
            The downloaded chunk as bytes.

        Raises:
            DownloadError: If an error occurs while downloading the chunk.
        """

        buffer = self._get_buffer()
        output_buffer = BytesIO()

        headers = {**self._custom_headers}
        chunk_size = end - start + 1

        try:
            if end > 0:
                headers['Range'] = f'bytes={start}-{end}'

            with self._client.stream('GET', url, headers=headers) as r:
                r.raise_for_status()
                downloaded = 0

                for chunk in r.iter_bytes(chunk_size=min(self._buffer_size, chunk_size)):
                    current_size = min(len(chunk), chunk_size - downloaded)

                    if current_size <= 0:
                        break

                    buffer[:current_size] = chunk[:current_size]
                    output_buffer.write(buffer[:current_size])
                    progress.update(task_id, advance=current_size)
                    downloaded += current_size

                    if downloaded >= chunk_size:
                        break

            return output_buffer.getvalue()
        except HTTPStatusError as e:
            raise DownloadError(f'An error occurred while downloading chunk: {str(e)}') from e
        finally:
            self._release_buffer(buffer)

    def download(
        self,
        url: str,
        output_path: Union[str, PathLike] = Path.cwd(),
        expected_hash: Optional[str] = None,
        hash_type: Literal[
            'md5',
            'sha1',
            'sha224',
            'sha256',
            'sha384',
            'sha512',
            'blake2b',
            'blake2s',
            'sha3_224',
            'sha3_256',
            'sha3_384',
            'sha3_512',
            'shake_128',
            'shake_256',
        ] = 'sha256',
    ) -> None:
        """
        Downloads a file from the provided URL to the output file path.

        - If the output_path is a directory, the file name will be generated from the server response.
        - If the output_path is a file, the file will be saved with the provided name.
        - If not provided, the file will be saved to the current working directory.

        Args:
            url: The download URL to download the file from. (required)
            output_path: The path to save the downloaded file to. If the path is a directory, the file name will be generated from the server response. If the path is a file, the file will be saved with the provided name. If not provided, the file will be saved to the current working directory. (default: Path.cwd())

        Raises:
            DownloadError: If an error occurs while downloading the file.
            HashVerificationError: If the hash of the downloaded file does not match the expected hash.
            RequestError: If an error occurs while getting file info.
        """

        try:
            output_path = Path(output_path)
            total_size, _, suggested_filename = self._get_file_info(url)

            if output_path.is_dir():
                output_path = Path(output_path, suggested_filename)

            if not self._overwrite:
                base_name = output_path.stem
                extension = output_path.suffix
                counter = 1

                while output_path.exists():
                    output_path = Path(output_path.parent, f'{base_name}_{counter}{extension}')
                    counter += 1

            self.output_path = output_path.as_posix()

            progress_columns = [
                TextColumn(output_path.name, style='magenta'),
                BarColumn(style='bold white', complete_style='bold red', finished_style='bold green'),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                TextColumn('[bold][progress.percentage]{task.percentage:>3.0f}%'),
            ]

            with Progress(*progress_columns, disable=not self._show_progress_bar) as progress:
                task_id = progress.add_task('download', total=total_size or 100, filename=output_path.name)

                if total_size == 0:
                    chunk = self._download_chunk(url, 0, 0, progress, task_id)
                    Path(output_path).write_bytes(chunk)
                else:
                    chunks = []
                    ranges = self._get_chunk_ranges(total_size)
                    connections = len(ranges)

                    with ThreadPoolExecutor(max_workers=connections) as executor:
                        futures = [
                            executor.submit(self._download_chunk, url, start, end, progress, task_id) for start, end in ranges
                        ]
                        chunks = [f.result() for f in futures]

                    with Path(output_path).open('wb') as fo:
                        for chunk in chunks:
                            fo.write(chunk)
        except KeyboardInterrupt:
            Path(output_path).unlink(missing_ok=True)
            self.output_path = None
            return
        except Exception as e:
            raise DownloadError(f'An error occurred while downloading file: {str(e)}') from e

        if expected_hash is not None:
            hasher = hashlib_new(hash_type)

            with Path(output_path).open('rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hasher.update(chunk)

            file_hash = hasher.hexdigest()

            if file_hash != expected_hash:
                Path(output_path).unlink(missing_ok=True)
                self.output_path = None

                raise HashVerificationError(
                    f'Hash verification failed. Hash type: "{hash_type}". Expected hash: "{expected_hash}". Actual hash: "{file_hash}"'
                )
