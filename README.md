## TurboDL

![PyPI - Version](https://img.shields.io/pypi/v/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Downloads](https://img.shields.io/pypi/dm/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Code Style](https://img.shields.io/badge/code%20style-ruff-blue?style=flat&logo=ruff&logoColor=blue&color=blue&link=https://github.com/astral-sh/ruff)
![PyPI - Format](https://img.shields.io/pypi/format/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Python Compatible Versions](https://img.shields.io/pypi/pyversions/turbodl?style=flat&logo=python&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)

TurboDL is an extremely smart, fast, and efficient download manager designed to optimize your downloading experience.

- **Smart Connection Management**: Dynamically calculates the optimal number of connections based on file size and network speed to maximize throughput
- **Intelligent Acceleration**: Built-in sophisticated download acceleration techniques that split downloads into multiple parallel streams
- **Automatic Retry System**: Efficiently retries failed requests with exponential backoff strategy to handle network instabilities
- **Pre-Download Intelligence**: Automatically detects file information, size, and type before download begins
- **Seamless Redirection**: Handles HTTP redirects automatically to ensure downloads complete successfully
- **Memory Optimization**: Intelligently uses RAM buffering to reduce disk I/O overhead and increase performance
- **Data Integrity**: Supports post-download hash verification (MD5, SHA256, etc.) to ensure file integrity
- **Real-time Feedback**: Provides an elegant, accurate progress bar with detailed download statistics
- **Cross-platform Compatibility**: Works consistently across all major operating systems

<br>

#### Installation (from [PyPI](https://pypi.org/project/turbodl))

```bash
pip install --upgrade turbodl  # Install the latest version of TurboDL
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

turbodl.output_path  # The absolute path to the downloaded file

```

#### Inside a Python script (Advanced Usage)

```python
from turbodl import TurboDL


turbodl = TurboDL(
    max_connections="auto",
    connection_speed_mbps=100,
    show_progress_bar=True,
)
turbodl.download(
    url="https://example.com/file.txt",
    output_path="path/to/file",
    pre_allocate_space=False,
    use_ram_buffer="auto",
    overwrite=True,
    headers=None,
    inactivity_timeout=120,
    timeout=None,
    expected_hash=None,
    hash_type="md5",
)

turbodl.output_path  # The absolute path to the downloaded file

```

#### From the command line

```bash
turbodl --help  # Show help for all commands
turbodl download --help  # Show help for the download command

turbodl download [...] https://example.com/file.txt path/to/file  # Download the file
```

##### CLI Demo

[![TurboDL CLI Demo](assets/demo.gif)](https://asciinema.org/a/hHUS4P1YwD1hdvk4BSfe444BI)

### Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, fork the repository and create a pull request. You can also simply open an issue and describe your ideas or report bugs. **Don't forget to give the project a star if you like it!**

<br>

<a href="https://github.com/henrique-coder/turbodl/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=henrique-coder/turbodl" />
</a>
