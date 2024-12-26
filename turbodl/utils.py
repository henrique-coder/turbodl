# Built-in imports
from io import BytesIO
from typing import Optional

# Third-party imports
from psutil import virtual_memory


class ChunkBuffer:
    """
    A class for buffering chunks of data.
    """

    def __init__(self, chunk_size_mb: int = 128, max_buffer_mb: int = 2048) -> None:
        """
        Initialize the ChunkBuffer class.

        Args:
            chunk_size_mb: The size of each chunk in megabytes.
            max_buffer_mb: The maximum size of the buffer in megabytes.
        """

        self.chunk_size = chunk_size_mb * 1024 * 1024
        self.max_buffer_size = min(max_buffer_mb * 1024 * 1024, virtual_memory().available * 0.25)
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

        if total_file_size <= self.max_buffer_size:
            if self.total_buffered >= total_file_size:
                chunk_data = self.current_buffer.getvalue()
                self.current_buffer = BytesIO()
                self.current_size = 0

                return chunk_data

            return None

        if self.current_size >= self.chunk_size:
            chunk_data = self.current_buffer.getvalue()
            self.current_buffer = BytesIO()
            self.current_size = 0

            return chunk_data

        return None
