# Standard modules
from collections.abc import Generator
from os import getenv
from pathlib import Path
from tempfile import TemporaryDirectory

# Third-party modules
from pytest import fixture

# Local modules
from src.turbodl import TurboDL


@fixture
def downloader() -> TurboDL:
    """Return a configured TurboDL instance."""

    return TurboDL(connection_speed_mbps=1000 if getenv("GITHUB_ACTIONS") in ("true", "1") else 700)


@fixture
def temporary_path() -> Generator:
    """Create a temporary directory for tests."""

    with TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)
