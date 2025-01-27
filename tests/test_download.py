# Built-in imports
from pathlib import Path

# Third-party imports
from pytest import raises

# Local imports
from turbodl import TurboDL
from turbodl.exceptions import TurboDLError


def test_invalid_url(downloader: TurboDL, temporary_path: Path) -> None:
    """
    Test download with invalid URL.
    """

    url: str = "https://invalid-url-that-does-not-exist.com/file.zip"

    with raises(TurboDLError):
        downloader.download(url=url, output_path=temporary_path)


def test_download_5mb_file(downloader: TurboDL, temporary_path: Path) -> None:
    """
    Test download of a 5MB file.
    """

    url: str = "http://212.183.159.230/5MB.zip"
    expected_filename: str = "5MB.zip"
    expected_hash: str = "b3215c06647bc550406a9c8ccc378756"
    hash_type: str = "md5"

    downloader.download(url=url, output_path=temporary_path, expected_hash=expected_hash, hash_type=hash_type)
    output_path = Path(downloader.output_path)

    assert output_path.name == expected_filename, f"URL: {url} - Output file name: {output_path.name} - Expected filename: {expected_filename} - Error: Downloaded file name is different than expected"


def test_download_35mb_file(downloader: TurboDL, temporary_path: Path) -> None:
    """
    Test download of a 35MB file.
    """

    url: str = "https://files.testfile.org/Video MP4/River - testfile.org.mp4"
    expected_filename: str = "River - testfile.org.mp4"
    expected_hash: str = "ac6ee07c343c36d0d0dbc65907252b2e"
    hash_type: str = "md5"

    downloader.download(url=url, output_path=temporary_path, expected_hash=expected_hash, hash_type=hash_type)
    output_path = Path(downloader.output_path)

    assert output_path.name == expected_filename, f"URL: {url} - Output file name: {output_path.name} - Expected filename: {expected_filename} - Error: Downloaded file name is different than expected"



def test_download_150mb_file(downloader: TurboDL, temporary_path: Path) -> None:
    """
    Test download of a 150MB file.
    """

    url: str = "https://files.testfile.org/ZIPC/150MB-Corrupt-Testfile.Org.zip"
    expected_filename: str = "150MB-Corrupt-Testfile.Org.zip"
    expected_hash: str = "b69f227f41579ba3594414dce1426f36"
    hash_type: str = "md5"

    downloader.download(url=url, output_path=temporary_path, expected_hash=expected_hash, hash_type=hash_type)
    output_path = Path(downloader.output_path)

    assert output_path.name == expected_filename, f"URL: {url} - Output file name: {output_path.name} - Expected filename: {expected_filename} - Error: Downloaded file name is different than expected"
