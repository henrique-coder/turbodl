# Standard modules
from logging import DEBUG, FileHandler, Formatter, NullHandler, getLogger
from os import PathLike
from pathlib import Path


class LogToFile:
    def __init__(self, log_file_path: str | PathLike | None, overwrite: bool = False) -> None:
        self._log_file_path: Path | None = Path(log_file_path) if log_file_path is not None else None
        self._overwrite: bool = overwrite

        self._setup_logger()

    def _setup_logger(self) -> None:
        logger = getLogger(__name__)
        logger.setLevel(DEBUG)

        if not self._log_file_path:
            logger.addHandler(NullHandler())
            self.logger = logger

            return None

        if not self._log_file_path.parent.exists():
            self._log_file_path.parent.mkdir(parents=True)

        if not logger.handlers:
            file_handler = FileHandler(self._log_file_path, mode="w" if self._overwrite else "a", encoding="utf-8")
            formatter = Formatter("[%(asctime)s.%(msecs)06d] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        self.logger = logger

    def info(self, message: str) -> None:
        if not self._log_file_path:
            return None

        self.logger.info(message)

    def error(self, message: str) -> None:
        if not self._log_file_path:
            return None

        self.logger.error(message)

    def warning(self, message: str) -> None:
        if not self._log_file_path:
            return None

        self.logger.warning(message)

    def debug(self, message: str) -> None:
        if not self._log_file_path:
            return None

        self.logger.debug(message)

    def blank_line(self, lines: int = 1) -> None:
        if not self._log_file_path:
            return None

        original_formatter = self.logger.handlers[0].formatter

        blank_formatter = Formatter("", datefmt="")
        self.logger.handlers[0].setFormatter(blank_formatter)

        for _ in range(lines):
            self.logger.info("")

        self.logger.handlers[0].setFormatter(original_formatter)
