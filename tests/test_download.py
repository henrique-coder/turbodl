# Built-in imports
from pathlib import Path

# Third-party imports
from pytest import mark, raises

# Local imports
from turbodl import TurboDL
from turbodl.exceptions import TurboDLError


TEST_FILES = [
    {
        "name": "5mb_file",
        "url": "https://files.testfile.org/anime.mp3",
        "expected_filename": "anime.mp3",
        "expected_hash": "b79c0a4d7d73e08f088876867315ecd8",
        "hash_type": "md5",
    },
    {
        "name": "30mb_file",
        "url": "https://files.testfile.org/ZIPC/30MB-Corrupt-Testfile.Org.zip",
        "expected_filename": "30MB-Corrupt-Testfile.Org.zip",
        "expected_hash": "e9643808139d7f95beee976fa263d551",
        "hash_type": "md5",
    },
    {
        "name": "50mb_file",
        "url": "https://files.testfile.org/PDF/50MB-TESTFILE.ORG.pdf",
        "expected_filename": "50MB-TESTFILE.ORG.pdf",
        "expected_hash": "eb405d3fee914fc235b835d2e01b5d62",
        "hash_type": "md5",
    },
]


def test_invalid_url(downloader: TurboDL, temporary_path: Path) -> None:
    """
    Test download with invalid URL.
    """

    url: str = "https://invalid-url-that-does-not-exist.com/file.zip"

    with raises(TurboDLError):
        downloader.download(url=url, output_path=temporary_path)


@mark.parametrize("file_info", TEST_FILES, ids=lambda x: f"{x['name']}_with_ram")
def test_download_file_with_ram(downloader: TurboDL, temporary_path: Path, file_info: dict) -> None:
    """
    Test file download with RAM buffer enabled.
    """

    downloader.download(
        url=file_info["url"],
        output_path=temporary_path,
        use_ram_buffer=True,
        expected_hash=file_info["expected_hash"],
        hash_type=file_info["hash_type"],
    )
    output_path = Path(downloader.output_path)

    assert output_path.name == file_info["expected_filename"], (
        f"URL: {file_info['url']} - "
        f"Output file name: {output_path.name} - "
        f"Expected filename: {file_info['expected_filename']} - "
        f"Error: Downloaded file name is different than expected"
    )


@mark.parametrize("file_info", TEST_FILES, ids=lambda x: f"{x['name']}_without_ram")
def test_download_file_without_ram(downloader: TurboDL, temporary_path: Path, file_info: dict) -> None:
    """
    Test file download with RAM buffer disabled.
    """

    downloader.download(
        url=file_info["url"],
        output_path=temporary_path,
        use_ram_buffer=False,
        expected_hash=file_info["expected_hash"],
        hash_type=file_info["hash_type"],
    )
    output_path = Path(downloader.output_path)

    assert output_path.name == file_info["expected_filename"], (
        f"URL: {file_info['url']} - "
        f"Output file name: {output_path.name} - "
        f"Expected filename: {file_info['expected_filename']} - "
        f"Error: Downloaded file name is different than expected"
    )
