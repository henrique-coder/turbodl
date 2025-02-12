# Standard modules
from collections.abc import Generator
from pathlib import Path
from tempfile import TemporaryDirectory

# Third-party modules
from pytest import fixture

# Local imports
from turbodl import TurboDL


@fixture
def downloader() -> TurboDL:
    """Return a configured TurboDL instance."""

    return TurboDL(max_connections="auto", connection_speed_mbps=1000, show_progress_bar=True)


@fixture
def temporary_path() -> Generator:
    """Create a temporary directory for tests."""

    with TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)
