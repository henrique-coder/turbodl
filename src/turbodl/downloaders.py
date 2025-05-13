# Standard modules
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from mmap import ACCESS_WRITE, mmap
from os import PathLike, ftruncate
from pathlib import Path
from threading import Lock

# Third-party modules
from httpx import Client
from rich.progress import Progress, TaskID

# Local modules
from .buffers import ChunkBuffer
from .utils import download_retry_decorator


def download_with_buffer_writer(output_path: str | PathLike, size_bytes: int, position: int, data: bytes) -> None:
    """
    Write the downloaded chunk to the file.

    Args:
        output_path: The path to the file.
        size_bytes: The size of the file in bytes.
        position: The position to start writing the data in the file.
        data: The data to be written.
    """

    with Path(output_path).open("r+b") as f:
        # Get the current size of the file
        current_size = f.seek(0, 2)

        # If the file is not large enough, truncate it to the correct size
        if current_size < size_bytes:
            ftruncate(f.fileno(), size_bytes)

        # Write the data to the file
        with mmap(f.fileno(), length=size_bytes, access=ACCESS_WRITE) as mm:
            mm[position : position + len(data)] = data

            # Flush the data to disk
            mm.flush()


@download_retry_decorator
def download_with_buffer_worker(
    http_client: Client,
    url: str,
    output_path: str | PathLike,
    size_bytes: int,
    chunk_buffers: dict[str, ChunkBuffer],
    write_positions: list[int],
    start: int,
    end: int,
    chunk_id: int,
    task_id: int,
    progress: Progress,
) -> None:
    """
    Worker function for downloading a file chunk using a buffer.

    Args:
        http_client: The HTTP client to use for the request.
        url: The URL of the file to download.
        output_path: The path to save the downloaded file.
        size_bytes: The total size of the file in bytes.
        chunk_buffers: A dictionary of chunk buffers.
        write_positions: List of write positions for each chunk.
        start: The start byte of the chunk.
        end: The end byte of the chunk.
        chunk_id: The ID of the chunk being processed.
        task_id: The task ID for progress tracking.
        progress: The progress tracker.
    """

    try:
        # Initialize a new buffer for the chunk
        chunk_buffers[chunk_id] = ChunkBuffer()

        if end > 0:
            # Set the range header for the HTTP request
            http_client.headers["Range"] = f"bytes={start}-{end}"

        # Stream the response from the server
        with http_client.stream("GET", url) as r:
            r.raise_for_status()  # Raise an error for bad responses

            # Iterate over the response data in 1MB chunks
            for data in r.iter_bytes(chunk_size=1024 * 1024):
                if not data:
                    break

                # Write data to the buffer and file if a complete chunk is available
                if complete_chunk := chunk_buffers[chunk_id].write(data, size_bytes):
                    download_with_buffer_writer(output_path, size_bytes, start + write_positions[chunk_id], complete_chunk)
                    write_positions[chunk_id] += len(complete_chunk)

                # Update the progress bar
                progress.update(TaskID(task_id), advance=len(data))

            # Write any remaining data in the buffer to the file
            if remaining := chunk_buffers[chunk_id].current_buffer.getvalue():
                download_with_buffer_writer(output_path, size_bytes, start + write_positions[chunk_id], remaining)
    finally:
        # Clean up the buffer to free memory
        if chunk_id in chunk_buffers and hasattr(chunk_buffers[chunk_id], "current_buffer"):
            chunk_buffers[chunk_id].current_buffer.close()


def download_with_buffer(
    http_client: Client,
    url: str,
    output_path: str | PathLike,
    size_bytes: int,
    chunk_buffers: dict[str, ChunkBuffer],
    chunk_ranges: Sequence[tuple[int, int]],
    task_id: int,
    progress: Progress,
) -> None:
    """
    Download a file using multiple buffered chunk downloads.

    Args:
        http_client: The HTTP client to use for the request.
        url: The URL of the file to download.
        output_path: The path to save the downloaded file.
        size_bytes: The total size of the file in bytes.
        chunk_buffers: A dictionary of chunk buffers.
        chunk_ranges: A sequence of (start, end) byte ranges for each chunk.
        task_id: The task ID for progress tracking.
        progress: The progress tracker.
    """

    # Initialize write positions for each chunk
    write_positions = [0] * len(chunk_ranges)

    # Use a thread pool to download each chunk in parallel
    with ThreadPoolExecutor(max_workers=len(chunk_ranges)) as executor:
        # Submit download tasks for each chunk range
        futures = [
            executor.submit(
                download_with_buffer_worker,
                http_client,
                url,
                output_path,
                size_bytes,
                chunk_buffers,
                write_positions,
                start,
                end,
                i,
                task_id,
                progress,
            )
            for i, (start, end) in enumerate(chunk_ranges)
        ]

        # Wait for all download tasks to complete
        for future in futures:
            future.result()


@download_retry_decorator
def download_without_buffer_worker(
    http_client: Client, url: str, output_path: str | PathLike, start: int, end: int, task_id: int, progress: Progress
) -> None:
    """
    Download a chunk of a file without using a buffer.

    Args:
        http_client: The HTTP client to use for the request.
        url: The URL of the file to download.
        output_path: The path to save the downloaded file.
        start: The start byte position of the chunk.
        end: The end byte position of the chunk.
        task_id: The task ID for progress tracking.
        progress: The progress tracker.
    """

    # Lock for writing to the file
    write_lock = Lock()

    # Set the Range header if end > 0
    if end > 0:
        http_client.headers["Range"] = f"bytes={start}-{end}"

    # Stream the request and write the response to the file
    with http_client.stream("GET", url) as r:
        r.raise_for_status()

        # Iterate over the chunks of the response and write them to the file
        for data in r.iter_bytes(chunk_size=1024 * 1024):
            chunk_len = len(data)

            # Acquire the write lock and seek to the correct position in the file
            with write_lock, Path(output_path).open("r+b") as fo:
                fo.seek(start)

                # Write the chunk to the file
                fo.write(data)

                # Advance the start position
                start += chunk_len

            # Update the progress tracker
            progress.update(TaskID(task_id), advance=chunk_len)


def download_without_buffer(
    http_client: Client,
    url: str,
    output_path: str | PathLike,
    chunk_ranges: Sequence[tuple[int, int]],
    task_id: int,
    progress: Progress,
) -> None:
    """
    Download a file in chunks using multiple threads and without using a buffer.

    Args:
        http_client: The HTTP client to use for the request.
        url: The URL of the file to download.
        output_path: The path to save the downloaded file.
        chunk_ranges: A sequence of (start, end) byte ranges for each chunk.
        task_id: The task ID for progress tracking.
        progress: The progress tracker.
    """

    # Use a thread pool to download each chunk in parallel
    with ThreadPoolExecutor(max_workers=len(chunk_ranges)) as executor:
        # Submit download tasks for each chunk range
        futures = [
            executor.submit(download_without_buffer_worker, http_client, url, output_path, start, end, task_id, progress)
            for start, end in chunk_ranges
        ]

        # Wait for all download tasks to complete
        for future in futures:
            try:
                # Raise any exceptions that occurred during the download
                future.result()
            except Exception as e:
                raise e
