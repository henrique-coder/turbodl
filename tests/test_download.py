# Standard modules
from pathlib import Path

# Third-party modules
from pytest import mark, raises

# Local modules
from src.turbodl import TurboDL
from src.turbodl.exceptions import TurboDLError


TEST_FILES = [
    {
        "name": "5mb_file",
        "url": "https://files.testfile.org/anime.mp3",
        "expectedFilename": "anime.mp3",
        "expectedHash": "b79c0a4d7d73e08f088876867315ecd8",
        "hashType": "md5",
    },
    {
        "name": "50mb_file",
        "url": "https://files.testfile.org/PDF/50MB-TESTFILE.ORG.pdf",
        "expectedFilename": "50MB-TESTFILE.ORG.pdf",
        "expectedHash": "eb405d3fee914fc235b835d2e01b5d62",
        "hashType": "md5",
    },
]


def test_invalid_url(downloader: TurboDL, temporary_path: Path) -> None:
    """Test download with invalid URL."""

    url: str = "https://invalid-url-that-does-not-exist.com/file.zip"

    with raises(TurboDLError):
        downloader.download(url=url, output_path=temporary_path)


@mark.parametrize("file_info", TEST_FILES, ids=lambda x: f"{x['name']}_with_ram")
def test_download_file_with_ram(downloader: TurboDL, temporary_path: Path, file_info: dict) -> None:
    """Test file download with RAM buffer enabled."""

    downloader.download(
        url=file_info["url"],
        output_path=temporary_path,
        enable_ram_buffer=True,
        expected_hash=file_info["expectedHash"],
        hash_type=file_info["hashType"],
    )
    output_path = Path(downloader.output_path)

    assert output_path.name == file_info["expectedFilename"], (
        f"URL: {file_info['url']} - "
        f"Output file name: {output_path.name} - "
        f"Expected filename: {file_info['expectedFilename']} - "
        f"Error: Downloaded file name is different than expected"
    )


@mark.parametrize("file_info", TEST_FILES, ids=lambda x: f"{x['name']}_without_ram")
def test_download_file_without_ram(downloader: TurboDL, temporary_path: Path, file_info: dict) -> None:
    """Test file download with RAM buffer disabled."""

    downloader.download(
        url=file_info["url"],
        output_path=temporary_path,
        enable_ram_buffer=False,
        expected_hash=file_info["expectedHash"],
        hash_type=file_info["hashType"],
    )
    output_path = Path(downloader.output_path)

    assert output_path.name == file_info["expectedFilename"], (
        f"URL: {file_info['url']} - "
        f"Output file name: {output_path.name} - "
        f"Expected filename: {file_info['expectedFilename']} - "
        f"Error: Downloaded file name is different than expected"
    )
