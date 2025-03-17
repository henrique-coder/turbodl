# Standard modules
from io import BytesIO
from time import time

# Third-party modules
from psutil import virtual_memory

# Local imports
from .constants import CHUNK_SIZE, MAX_BUFFER_SIZE, MAX_RAM_USAGE


class ChunkBuffer:
    """A ChunkBuffer is a memory buffer that stores a chunk of a file being downloaded."""

    def __init__(self, chunk_size_bytes: int = CHUNK_SIZE, max_buffer_size_bytes: int = MAX_BUFFER_SIZE) -> None:
        """
        Initialize a ChunkBuffer with the given chunk size and max buffer size.

        Args:
            chunk_size_bytes (int): The maximum size of each chunk in bytes.
            max_buffer_size_bytes (int): The maximum size of the buffer in bytes.
        """

        self.chunk_size = chunk_size_bytes

        # Make sure the max buffer size is not larger than the available memory
        self.max_buffer_size = min(max_buffer_size_bytes, int(virtual_memory().available * MAX_RAM_USAGE))

        # Initialize the buffer
        self.current_buffer = BytesIO()
        self.current_size = 0
        self.total_buffered = 0
        self.last_activity_time = time()

    def write(self, data: bytes, total_file_size_bytes: int) -> bytes | None:
        """
        Write data to the buffer, and return a chunk of data if the buffer is full.

        Args:
            data (bytes): The data to write to the buffer.
            total_file_size_bytes (int): The total size of the file in bytes.

        Returns:
            bytes | None: A chunk of data if the buffer is full, otherwise None.
        """

        self.last_activity_time = time()

        data_size = len(data)

        # If the buffer is full, return None
        if self.current_size + data_size > self.max_buffer_size:
            return None

        # If we've already written more data than the total file size, return None
        if self.total_buffered + data_size > total_file_size_bytes:
            return None

        # Write the data to the buffer
        self.current_buffer.write(data)
        self.current_size += data_size
        self.total_buffered += data_size

        # If the buffer is full, return the chunk of data
        if (
            self.current_size >= self.chunk_size
            or self.total_buffered >= total_file_size_bytes
            or self.current_size >= self.max_buffer_size
        ):
            chunk_data = self.current_buffer.getvalue()

            # Clear the buffer
            self.current_buffer.close()
            self.current_buffer = BytesIO()
            self.current_size = 0

            return chunk_data

        return None

    def reset_buffer(self) -> None:
        """Reset the buffer to free memory without losing tracking information."""

        if self.current_size > 0:
            # Preserve the data if there's any
            data = self.current_buffer.getvalue()
            self.current_buffer.close()
            self.current_buffer = BytesIO()
            self.current_buffer.write(data)
        else:
            # Just create a new empty buffer
            self.current_buffer.close()
            self.current_buffer = BytesIO()

    def __del__(self) -> None:
        """Destructor for the ChunkBuffer. Closes the BytesIO object to free up memory."""

        if hasattr(self, "current_buffer"):
            # Close the BytesIO object to free up memory
            self.current_buffer.close()
