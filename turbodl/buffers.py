# Standard modules
from io import BytesIO

# Third-party modules
from psutil import virtual_memory


class ChunkBuffer:
    def __init__(self, chunk_size_bytes: int = 256 * (1024**2), max_buffer_bytes: int = 1 * (1024**3)) -> None:
        self.chunk_size = chunk_size_bytes
        self.max_buffer_size = min(max_buffer_bytes, virtual_memory().available * 0.30)
        self.current_buffer = BytesIO()
        self.current_size = 0
        self.total_buffered = 0

    def write(self, data: bytes, total_file_size_bytes: int) -> bytes | None:
        data_size = len(data)

        if self.current_size + data_size > self.max_buffer_size or self.total_buffered + data_size > self.max_buffer_size:
            return None

        if self.total_buffered + data_size > total_file_size_bytes:
            return None

        self.current_buffer.write(data)
        self.current_size += data_size
        self.total_buffered += data_size

        if (
            self.current_size >= self.chunk_size
            or self.total_buffered >= total_file_size_bytes
            or self.current_size >= self.max_buffer_size
        ):
            chunk_data = self.current_buffer.getvalue()

            self.current_buffer.close()
            self.current_buffer = BytesIO()
            self.current_size = 0

            return chunk_data

        return None
