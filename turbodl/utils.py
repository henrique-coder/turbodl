# Built-in imports
from io import BytesIO
from typing import Optional


class ChunkBuffer:
    def __init__(self, chunk_size_mb: int = 128) -> None:
        self.chunk_size = chunk_size_mb * 1024 * 1024
        self.current_buffer = BytesIO()
        self.current_size = 0

    def write(self, data: bytes) -> Optional[bytes]:
        self.current_buffer.write(data)
        self.current_size += len(data)

        if self.current_size >= self.chunk_size:
            chunk_data = self.current_buffer.getvalue()

            self.current_buffer = BytesIO()
            self.current_size = 0

            return chunk_data

        return None
