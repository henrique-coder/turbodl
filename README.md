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
- Supports post-download hash verification.
- Automatically uses RAM buffer to speed up downloads and reduce disk I/O overhead.
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
# >>> Downloading "file.txt" ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 25.2/25.2 MB 82.6 MB/s 0:00:00 0:00:01 100% (with RAM buffer, writing to DISK)

print(turbodl.output_path)  # The resolved and absolute path to the downloaded file
# >>> absolute/path/to/file.txt

```

#### Inside a Python script (Advanced Usage)

```python
from turbodl import TurboDL


turbodl = TurboDL(
    max_connections="auto",
    connection_speed=80,
    show_progress_bars=True,
    custom_headers=None,
    timeout=None
)
turbodl.download(
    url="https://example.com/file.txt",
    output_path="path/to/file",
    pre_allocate_space=False,
    use_ram_buffer="auto",
    overwrite=True,
    expected_hash=None,
    hash_type="md5",
)
# >>> Downloading "file.txt" ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 25.2/25.2 MB 82.6 MB/s 0:00:00 0:00:01 100% (with RAM buffer, writing to DISK)

print(turbodl.output_path)  # The resolved and absolute path to the downloaded file
# >>> absolute/path/to/file.txt

```

#### From the command line

```bash
turbodl --help
# >>>  Usage: turbodl [OPTIONS] COMMAND [ARGS]...
# >>>
# >>>  TurboDL is an extremely smart, fast, and efficient download manager with several automations.
# >>>
# >>>  Examples:
# >>>     Download a file:
# >>>     $ turbodl download https://example.com/file.zip
# >>>
# >>>     Download a file to a specific path:
# >>>     $ turbodl download https://example.com/file.zip /path/to/file
# >>>
# >>>  More Help:
# >>>     For detailed download options, use:
# >>>     $ turbodl download --help
# >>>
# >>> ╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
# >>> │ --version  -v        Show version and exit.                                                                                                                                                                             │
# >>> │ --help     -h        Show this message and exit.                                                                                                                                                                        │
# >>> ╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
# >>> ╭─ Commands ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
# >>> │ check      Check for available updates.                                                                                                                                                                                 │
# >>> │ download   Download a file from the provided URL to the specified output path (with a lot of options)                                                                                                                   │
# >>> ╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

turbodl download --help
# >>>  Usage: turbodl download [OPTIONS] URL [OUTPUT_PATH]
# >>>
# >>>  Download a file from the provided URL to the specified output path (with a lot of options)
# >>>
# >>> ╭─ Arguments ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
# >>> │ *    url              TEXT           Download URL. [default: None] [required]                                                                                                                                           │
# >>> │      output_path      [OUTPUT_PATH]  Destination path. If directory, filename is derived from server response. [default: (Current directory)]                                                                           │
# >>> ╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
# >>> ╭─ Options ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
# >>> │ --max-connections     -mc       TEXT     Max connections: 'auto' or integer (1-24). [default: auto]                                                                                                                     │
# >>> │ --connection-speed    -cs       FLOAT    Connection speed in Mbps for optimal connections. [default: 80]                                                                                                                │
# >>> │ --hide-progress-bars  -hpb               Hide progress bars (shown by default).                                                                                                                                         │
# >>> │ --pre-allocate-space  -pas               Pre-allocate disk space before downloading.                                                                                                                                    │
# >>> │ --auto-ram-buffer     -arb               Use RAM buffer automatically if path isn't RAM dir (default).                                                                                                                  │
# >>> │ --use-ram-buffer      -urb               Always use RAM buffer.                                                                                                                                                         │
# >>> │ --no-ram-buffer       -nrb               Never use RAM buffer.                                                                                                                                                          │
# >>> │ --no-overwrite        -no                Don't overwrite existing files (overwrite by default).                                                                                                                         │
# >>> │ --timeout             -t        INTEGER  Download timeout in seconds. [default: None]                                                                                                                                   │
# >>> │ --expected-hash       -eh       TEXT     Expected file hash for verification. [default: None]                                                                                                                           │
# >>> │ --hash-type           -ht       TEXT     Hash algorithm for verification. [default: md5]                                                                                                                                │
# >>> │ --help                -h                 Show this message and exit.                                                                                                                                                    │
# >>> ╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

turbodl download [...] https://example.com/file.txt path/to/file
# >>> Downloading "file.txt" ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 25.2/25.2 MB 82.6 MB/s 0:00:00 0:00:01 100% (with RAM buffer, writing to DISK)
```

### Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, fork the repository and create a pull request. You can also simply open an issue and describe your ideas or report bugs. **Don't forget to give the project a star if you like it!**

1. Fork the project;
2. Create your feature branch ・ `git checkout -b feature/{feature_name}`;
3. Commit your changes ・ `git commit -m "{commit_message}"`;
4. Push to the branch ・ `git push origin feature/{feature_name}`;
5. Open a pull request, describing the changes you made and wait for a review.
