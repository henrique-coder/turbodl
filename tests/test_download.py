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
        "url": "http://212.183.159.230/5MB.zip",
        "expected_filename": "5MB.zip",
        "expected_hash": "b3215c06647bc550406a9c8ccc378756",
        "hash_type": "md5",
    },
    {
        "name": "35mb_file",
        "url": "https://files.testfile.org/Video MP4/River - testfile.org.mp4",
        "expected_filename": "River - testfile.org.mp4",
        "expected_hash": "ac6ee07c343c36d0d0dbc65907252b2e",
        "hash_type": "md5",
    },
    {
        "name": "150mb_file",
        "url": "https://files.testfile.org/ZIPC/150MB-Corrupt-Testfile.Org.zip",
        "expected_filename": "150MB-Corrupt-Testfile.Org.zip",
        "expected_hash": "b69f227f41579ba3594414dce1426f36",
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


@mark.parametrize("file_info", TEST_FILES, ids=lambda x: x["name"])
def test_download_file(downloader: TurboDL, temporary_path: Path, file_info: dict) -> None:
    """
    Test file download with different sizes.
    """

    downloader.download(
        url=file_info["url"],
        output_path=temporary_path,
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
