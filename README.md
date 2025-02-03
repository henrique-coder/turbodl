## TurboDL

![PyPI - Version](https://img.shields.io/pypi/v/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Downloads](https://img.shields.io/pypi/dm/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Code Style](https://img.shields.io/badge/code%20style-ruff-blue?style=flat&logo=ruff&logoColor=blue&color=blue&link=https://github.com/astral-sh/ruff)
![PyPI - Format](https://img.shields.io/pypi/format/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Python Compatible Versions](https://img.shields.io/pypi/pyversions/turbodl?style=flat&logo=python&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)

TurboDL is an extremely smart, fast, and efficient download manager with several automations.

- Built-in sophisticated download acceleration technique.
- Uses a sophisticated algorithm to calculate the optimal number of connections based on file size and connection speed.
- Retry failed requests efficiently.
- Automatically detects file information before download.
- Automatically handles redirects.
- Automatically uses RAM buffer to speed up downloads and reduce disk I/O overhead.
- Supports post-download hash verification.
- Accurately displays a beautiful progress bar.

<br>

#### Installation (from [PyPI](https://pypi.org/project/turbodl))

```bash
pip install -U turbodl  # Install the latest version of TurboDL
```

### Example Usage

#### Inside a Python script (Basic Usage)

```python
from turbodl import TurboDL


turbodl = TurboDL()
turbodl.download(
    url="https://example.com/file.txt",  # Your download URL
    output_path="path/to/file"  # The file/path to save the downloaded file to or leave it empty to save it to the current working directory
)

print(turbodl.output_path)  # The absolute path to the downloaded file

```

#### Inside a Python script (Advanced Usage)

```python
from turbodl import TurboDL


turbodl = TurboDL(
    max_connections="auto",
    connection_speed_mbps=80,
    show_progress_bar=True,
    save_log_file=False,
)
turbodl.download(
    url="https://example.com/file.txt",
    output_path="path/to/file",
    pre_allocate_space=False,
    use_ram_buffer="auto",
    overwrite=True,
    headers=None,
    timeout=None
    expected_hash=None,
    hash_type="md5",
)

print(turbodl.output_path)  # The absolute path to the downloaded file

```

#### From the command line

```bash
turbodl --help  # Show help for all commands
turbodl download --help  # Show help for the download command

turbodl download [...] https://example.com/file.txt path/to/file  # Download the file
```

##### CLI Demo

[![TurboDL CLI Demo](https://i.imgur.com/xZt5k1V.gif)](https://asciinema.org/a/701070)

### Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, fork the repository and create a pull request. You can also simply open an issue and describe your ideas or report bugs. **Don't forget to give the project a star if you like it!**

<br>

<a href="https://github.com/henrique-coder/turbodl/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=henrique-coder/turbodl" />
</a>
