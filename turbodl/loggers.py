# Standard modules
from logging import DEBUG, FileHandler, Formatter, NullHandler, getLogger
from os import PathLike
from pathlib import Path


class FileLogger:
    def __init__(self, log_file_path: str | PathLike | None, overwrite: bool = False) -> None:
        self.log_file_path: Path | None = Path(log_file_path) if log_file_path is not None else None
        self.overwrite: bool = overwrite
        self._setup_logger()

    def _setup_logger(self) -> None:
        logger = getLogger(__name__)
        logger.setLevel(DEBUG)

        if not self.log_file_path:
            logger.addHandler(NullHandler())
            self.logger = logger

            return None

        if not self.log_file_path.parent.exists():
            self.log_file_path.parent.mkdir(parents=True)

        if not logger.handlers:
            file_handler = FileHandler(self.log_file_path, mode="w" if self.overwrite else "a", encoding="utf-8")
            formatter = Formatter("[%(asctime)s.%(msecs)06d] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        self.logger = logger

    def info(self, message: str) -> None:
        if not self.log_file_path:
            return None

        self.logger.info(message)

    def error(self, message: str) -> None:
        if not self.log_file_path:
            return None

        self.logger.error(message)

    def warning(self, message: str) -> None:
        if not self.log_file_path:
            return None

        self.logger.warning(message)

    def debug(self, message: str) -> None:
        if not self.log_file_path:
            return None

        self.logger.debug(message)
