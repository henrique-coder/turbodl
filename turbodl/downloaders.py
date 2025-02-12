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

# Local imports
from .buffers import ChunkBuffer
from .loggers import LogToFile
from .utils import download_retry_decorator


def download_with_buffer_writer(
    output_path: str | PathLike, size_bytes: int, position: int, data: bytes, logger: LogToFile
) -> None:
    logger.debug(f"Writing {len(data)} bytes to {output_path} at position {position}")

    with Path(output_path).open("r+b") as f:
        current_size = f.seek(0, 2)

        if current_size < size_bytes:
            logger.debug(f"Pre-allocating file space to {size_bytes}")

            ftruncate(f.fileno(), size_bytes)

        with mmap(f.fileno(), length=size_bytes, access=ACCESS_WRITE) as mm:
            mm[position : position + len(data)] = data
            mm.flush()

            logger.debug(f"Finished writing {len(data)} bytes to {output_path}")


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
    logger: LogToFile,
) -> None:
    logger.info(f"Starting thread for chunk {chunk_id + 1}")

    chunk_buffers[chunk_id] = ChunkBuffer()

    if end > 0:
        http_client.headers["Range"] = f"bytes={start}-{end}"

    with http_client.stream("GET", url) as r:
        r.raise_for_status()

        for data in r.iter_bytes(chunk_size=1024 * 1024):
            logger.debug(f"Received {len(data)} bytes for chunk {chunk_id + 1}")

            if complete_chunk := chunk_buffers[chunk_id].write(data, size_bytes):
                download_with_buffer_writer(output_path, size_bytes, start + write_positions[chunk_id], complete_chunk, logger)

                logger.debug(f"Wrote {len(complete_chunk)} bytes to file")

                write_positions[chunk_id] += len(complete_chunk)

            progress.update(TaskID(task_id), advance=len(data))

        if remaining := chunk_buffers[chunk_id].current_buffer.getvalue():
            download_with_buffer_writer(output_path, size_bytes, start + write_positions[chunk_id], remaining, logger)
            logger.debug(f"Wrote {len(remaining)} bytes remaining to file")

        logger.debug(f"Finished thread for chunk {chunk_id + 1}")


def download_with_buffer(
    http_client: Client,
    url: str,
    output_path: str | PathLike,
    size_bytes: int,
    chunk_buffers: dict[str, ChunkBuffer],
    chunk_ranges: Sequence[tuple[int, int]],
    task_id: int,
    progress: Progress,
    logger: LogToFile,
) -> None:
    write_positions = [0] * len(chunk_ranges)

    logger.info("Starting download with RAM buffer")

    with ThreadPoolExecutor(max_workers=len(chunk_ranges)) as executor:
        for future in [
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
                logger,
            )
            for i, (start, end) in enumerate(chunk_ranges)
        ]:
            future.result()


@download_retry_decorator
def download_without_buffer_worker(
    http_client: Client,
    url: str,
    output_path: str | PathLike,
    start: int,
    end: int,
    task_id: int,
    progress: Progress,
    logger: LogToFile,
) -> None:
    write_lock = Lock()

    if end > 0:
        http_client.headers["Range"] = f"bytes={start}-{end}"

    with http_client.stream("GET", url) as r:
        r.raise_for_status()

        for data in r.iter_bytes(chunk_size=1024 * 1024):
            chunk_len = len(data)

            logger.debug(f"Received {chunk_len} bytes for chunk {start}-{end}")

            with write_lock, Path(output_path).open("r+b") as fo:
                fo.seek(start)
                fo.write(data)
                start += chunk_len

            logger.debug(f"Wrote {chunk_len} bytes to file at position {start}")

            progress.update(TaskID(task_id), advance=chunk_len)


def download_without_buffer(
    http_client: Client,
    url: str,
    output_path: str | PathLike,
    chunk_ranges: Sequence[tuple[int, int]],
    task_id: int,
    progress: Progress,
    logger: LogToFile,
) -> None:
    logger.info("Starting download without buffer")

    with ThreadPoolExecutor(max_workers=len(chunk_ranges)) as executor:
        futures = [
            executor.submit(download_without_buffer_worker, http_client, url, output_path, start, end, task_id, progress, logger)
            for start, end in chunk_ranges
        ]

        for future in futures:
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error in download_without_buffer_worker: {e}")

                raise e

    logger.info("Completed download without buffer")
