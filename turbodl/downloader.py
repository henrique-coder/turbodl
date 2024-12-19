# Built-in imports
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from math import ceil
from mimetypes import guess_extension as guess_mimetype_extension
from os import PathLike
from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple, Union
from urllib.parse import unquote, urlparse

# Third-party imports
from httpx import Client, HTTPStatusError
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn, TransferSpeedColumn
from tenacity import retry, stop_after_attempt, wait_exponential

# Local imports
from .exceptions import DownloadError, RequestError


class TurboDL:
    """A class for downloading direct download URLs."""

    def __init__(
        self,
        max_connections: Union[int, Literal['auto']] = 'auto',
        connection_speed: float = 80,
        overwrite: bool = True,
        show_progress_bar: bool = True,
        custom_headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Initialize the class with the required settings for downloading a file.

        Args:
            max_connections: The maximum number of connections to use for downloading the file. (default: 'auto')
            connection_speed: The connection speed in Mbps. (default: 80)
            overwrite: Overwrite the file if it already exists. Otherwise, a "_1", "_2", etc. suffix will be added. (default: True)
            show_progress_bar: Show or hide the download progress bar. (default: True)
            custom_headers: Custom headers to include in the request. If None, default headers will be used. Imutable headers are 'Accept-Encoding' and 'Range'. (default: None)
            timeout: Timeout in seconds for the download process. Or None for no timeout. (default: None)
        """

        self._max_connections: Union[int, Literal['auto']] = max_connections
        self._connection_speed: int = connection_speed
        self._overwrite: bool = overwrite
        self._show_progress_bar: bool = show_progress_bar
        self._timeout: Optional[int] = timeout

        imutable_headers = ['Accept-Encoding', 'Range']

        self._custom_headers: Dict[str, str] = {
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }

        if custom_headers:
            for key, value in custom_headers.items():
                if key.title() not in imutable_headers:
                    self._custom_headers[key.title()] = value

        self._client: Client = Client(headers=self._custom_headers, follow_redirects=True, timeout=self._timeout)

        self.output_path: str = None

    @lru_cache()
    def _calculate_connections(self, file_size: int, connection_speed: Union[float, Literal['auto']]) -> int:
        """
        Calculates optimal number of connections based on file size and connection speed.

        - The connection speed ranges and recommended connections:

        | Connection Speed | Base Multiplier |
        | ---------------- | --------------- |
        | < 10 Mbps        | 0.2x            |
        | 10-50 Mbps       | 0.4x            |
        | 50-100 Mbps      | 0.6x            |
        | 100-300 Mbps     | 0.8x            |
        | 300-500 Mbps     | 1.0x            |
        | > 500 Mbps       | 1.2x            |

        - Example outputs for different connection speeds and file sizes:

        | Connection Speed | 1MB file  | 10MB file  | 100MB file  | 500MB file  |
        | ---------------- | --------- | ---------- | ----------- | ----------- |
        | 10 Mbps          | 1         | 3          | 6           | 13          |
        | 50 Mbps          | 2         | 3          | 6           | 13          |
        | 100 Mbps         | 2         | 5          | 10          | 19          |
        | 300 Mbps         | 3         | 6          | 13          | 26          |
        | 500 Mbps         | 4         | 8          | 16          | 32          |
        | 1000 Mbps        | 4         | 9          | 19          | 32          |

        Args:
            file_size: The size of the file to download. (required)
            connection_speed: The connection speed in Mbps. (default: 80)

        Returns:
            The number of connections to use.
        """

        if self._max_connections != 'auto':
            return self._max_connections

        file_size_mb = file_size / (1024 * 1024)

        if file_size_mb < 1:
            base_connections = 1
        elif file_size_mb <= 5:
            base_connections = 4
        elif file_size_mb <= 50:
            base_connections = 8
        elif file_size_mb <= 200:
            base_connections = 16
        elif file_size_mb <= 400:
            base_connections = 24
        else:
            base_connections = 32

        speed = 80.0 if connection_speed == 'auto' else float(connection_speed)

        if speed < 10:
            multiplier = 0.2
        elif speed <= 50:
            multiplier = 0.4
        elif speed <= 100:
            multiplier = 0.6
        elif speed <= 300:
            multiplier = 0.8
        elif speed <= 500:
            multiplier = 1.0
        else:
            multiplier = 1.2

        return max(1, min(int(base_connections * multiplier), 32))

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
            r = self._client.head(url)
            r.raise_for_status()
        except HTTPStatusError as e:
            raise RequestError(f'An error occurred while getting file info: {str(e)}') from e

        content_length = int(r.headers.get('content-length', 0))
        content_type = r.headers.get('content-type', 'application/octet-stream').split(';')[0]
        content_disposition = r.headers.get('content-disposition')

        if content_disposition and 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[-1].strip('"\'')
        else:
            path = unquote(urlparse(url).path)
            filename = Path(path).name

            if not filename:
                extension = guess_mimetype_extension(content_type)

                if extension:
                    filename = 'downloaded_file' + extension

        return (content_length, content_type, filename)

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

        optimal_chunk = max(1024 * 1024, total_size // (connections * 2))
        chunk_size = min(ceil(total_size / connections), optimal_chunk)

        ranges = []
        start = 0

        while start < total_size:
            end = min(start + chunk_size - 1, total_size - 1)
            ranges.append((start, end))
            start = end + 1

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

        headers = {**self._custom_headers}

        chunk_size = min(8192, end - start + 1)
        buffer = bytearray()

        if end > 0:
            headers['Range'] = f'bytes={start}-{end}'

        try:
            with self._client.stream('GET', url, headers=headers) as r:
                r.raise_for_status()

                for chunk in r.iter_bytes(chunk_size=chunk_size):
                    buffer.extend(chunk)
                    progress.update(task_id, advance=len(chunk))

            return bytes(buffer)
        except HTTPStatusError as e:
            raise DownloadError(f'An error occurred while downloading chunk: {str(e)}') from e

    def download(self, url: str, output_path: Union[str, PathLike] = Path.cwd()) -> None:
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
            RequestError: If an error occurs while getting file info.
        """

        try:
            total_size, mime_type, suggested_filename = self._get_file_info(url)
            output_path = Path(output_path)

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
                TextColumn(f'Downloading a {mime_type.split("/")[0] if mime_type else "unknown"} file ({mime_type})'),
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
            ]

            with Progress(*progress_columns, disable=not self._show_progress_bar) as progress:
                task_id = progress.add_task('download', total=total_size or 100, filename=output_path.name, mime=mime_type)

                if total_size == 0:
                    chunk = self._download_chunk(url, 0, 0, progress, task_id)

                    with Path(output_path).open('wb') as fo:
                        fo.write(chunk)
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
        except Exception as e:
            raise DownloadError(f'An error occurred while downloading file: {str(e)}') from e
