# TurboDL

![PyPI - Version](https://img.shields.io/pypi/v/turbodl?style=for-the-badge&logo=pypi&logoColor=white&color=blue)
![PyPI - Downloads](https://img.shields.io/pypi/dm/turbodl?style=for-the-badge&logo=pypi&logoColor=white&color=blue)
![Python Versions](https://img.shields.io/pypi/pyversions/turbodl?style=for-the-badge&logo=python&logoColor=white&color=blue)
![License](https://img.shields.io/github/license/henrique-coder/turbodl?style=for-the-badge&color=blue)

## 🚀 Overview

TurboDL is an extremely smart, fast, and efficient download manager designed to optimize your downloading experience.

## ✨ Key Features

- **Smart Connection Management**: Dynamically calculates the optimal number of connections based on file size and network speed
- **Intelligent Acceleration**: Built-in sophisticated download acceleration techniques that split downloads into multiple parallel streams
- **Automatic Retry System**: Efficiently retries failed requests with exponential backoff strategy
- **Pre-Download Intelligence**: Automatically detects file information, size, and type before download begins
- **Seamless Redirection**: Handles HTTP redirects automatically for successful downloads
- **Memory Optimization**: Intelligently uses RAM buffering to reduce disk I/O overhead
- **Data Integrity**: Supports post-download hash verification (MD5, SHA256, etc.)
- **Real-time Feedback**: Provides an elegant, accurate progress bar with detailed statistics
- **Cross-platform Compatibility**: Works consistently across all major operating systems

## 📦 Installation

```bash
pip install --upgrade turbodl  # Install the latest version of TurboDL
```

## 🔍 Examples

### Basic Usage

```python
from turbodl import TurboDL

turbodl = TurboDL()
turbodl.download(
    url="https://example.com/file.txt",  # Your download URL
    output_path="path/to/file"  # The file/path to save the downloaded file
)

# Access the absolute path to the downloaded file
print(turbodl.output_path)
```

### Advanced Usage

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

# Access the absolute path to the downloaded file
print(turbodl.output_path)
```

## Command Line Interface

```bash
# Show help for all commands
turbodl --help

# Show help for the download command
turbodl download --help

# Download a file
turbodl download [...] https://example.com/file.txt path/to/file
```

## 📊 CLI Demo

[![TurboDL CLI Demo](assets/demo.gif)](https://asciinema.org/a/hHUS4P1YwD1hdvk4BSfe444BI)

## 📋 Parameters

### `TurboDL` Class Parameters

| Parameter | Type | Default | Description |
| - | - | - | - |
| `max_connections` | int, Literal["auto"] | "auto" | Maximum connections for parallel downloading. Minimum is 1 and maximum is 32. |
| `connection_speed_mbps` | float | 100 | Your current internet connection speed in Mbps. |
| `show_progress_bar` | bool | True | Whether to display a progress bar. |

### `Download` Method Parameters

| Parameter | Type | Default | Description |
| - | - | - | - |
| `url` | str | - | The URL of the file to download. |
| `output_path` | str, PathLike, None | None | The path to save the downloaded file. If it is a directory, filename is derived from server response. If None, the current working directory is used. |
| `pre_allocate_space` | bool | False | Whether to pre-allocate disk space for the file. |
| `use_ram_buffer` | bool, Literal["auto"] | "auto" | Use RAM buffer for download. If set to False, the file will be downloaded continuously to disk. If set to True, the file will be downloaded with the help of RAM memory. If set to "auto", the RAM buffer will be disabled if the output path is a RAM directory and enabled otherwise. |
| `overwrite` | bool | True | Whether to overwrite the file if it already exists. |
| `headers` | dict[str, str], None | None | A dictionary of headers to include in the request. |
| `inactivity_timeout` | int | 120 | Timeout in seconds after the connection is considered idle. None means no timeout. |
| `timeout` | int | None | Overall timeout in seconds. None means no timeout. |
| `expected_hash` | str, None | None | The expected hash value of the downloaded file. If provided, the file will be verified after download. |
| `hash_type` | Literal["md5", "sha1", "sha224", "sha256", "sha384", "sha512", "blake2b", "blake2s", "sha3_224", "sha3_256", "sha3_384", "sha3_512", "shake_128", "shake_256"] | "md5" | Hash algorithm to use for verification. Available: md5, sha1, sha224, sha256, sha384, sha512, blake2b, blake2s, sha3_224, sha3_256, sha3_384, sha3_512, shake_128, shake_256. |

## 🛠️ Development

```bash
# Clone the repository
git clone https://github.com/henrique-coder/turbodl.git
cd turbodl

# Install Poetry in your local environment
pip install --upgrade poetry

# Install project dependencies
make install

# Run tests
make tests

# Lint and format code
make lint
make format
```

## 🤝 Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 👥 Contributors

<a href="https://github.com/henrique-coder/turbodl/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=henrique-coder/turbodl" />
</a>

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📊 Project Status

TurboDL is in active development. Check the [releases page](https://github.com/henrique-coder/turbodl/releases) for the latest updates.

## 🌟 Star the Project

If you find this project useful, please consider giving it a star on [GitHub](https://github.com/henrique-coder/turbodl).
