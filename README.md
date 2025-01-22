## TurboDL

![PyPI - Version](https://img.shields.io/pypi/v/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Downloads](https://img.shields.io/pypi/dm/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Code Style](https://img.shields.io/badge/code%20style-ruff-blue?style=flat&logo=ruff&logoColor=blue&color=blue&link=https://github.com/astral-sh/ruff)
![PyPI - Format](https://img.shields.io/pypi/format/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Python Compatible Versions](https://img.shields.io/pypi/pyversions/turbodl?style=flat&logo=python&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)

TurboDL is an extremely smart, fast and efficient download manager with several automations.

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
# >>> Downloading "file.txt" ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 25.2/25.2 MB 82.6 MB/s 0:00:00 100%

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
    use_ram_buffer=True,
    overwrite=True,
    expected_hash=None,
    hash_type="md5",
)
# >>> Downloading "file.txt" ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 25.2/25.2 MB 82.6 MB/s 0:00:00 100%

print(turbodl.output_path)  # The resolved and absolute path to the downloaded file
# >>> absolute/path/to/file.txt

```

#### From the command line

```bash
turbodl --help
# >>>  Usage: turbodl [OPTIONS] URL [OUTPUT_PATH]
# >>>
# >>> ╭─ Arguments ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
# >>> │ *    url              TEXT           The download URL to download the file from. [required]                                                                                                                                   │
# >>> │      output_path      [OUTPUT_PATH]  The path to save the downloaded file to. If the path is a directory, the file name will be generated from the server response. If the path is a file, the file will be saved with the    │
# >>> │                                      provided name. If not provided, the file will be saved to the current working directory.                                                                                                 │
# >>> │                                      [default: (Current working directory)]                                                                                                                                                   │
# >>> ╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
# >>> ╭─ Options ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
# >>> │ --max-connections     -mc                                   TEXT     The maximum number of connections to use for downloading the file ('auto' will dynamically calculate the number of connections based on the file size    │
# >>> │                                                                      and connection speed and an integer between 1 and 24 will set the number of connections to that value).                                                  │
# >>> │                                                                      [default: auto]                                                                                                                                          │
# >>> │ --connection-speed    -cs                                   FLOAT    Your connection speed in Mbps (megabits per second) (your connection speed will be used to help calculate the optimal number of connections).            │
# >>> │                                                                      [default: 80]                                                                                                                                            │
# >>> │ --show-progress-bars  -spb  --hide-progress-bars     -hpb            Show or hide all progress bars. [default: show-progress-bars]                                                                                            │
# >>> │ --timeout             -t                                    INTEGER  Timeout in seconds for the download process. Or None for no timeout. [default: (No timeout)]                                                             │
# >>> │ --pre-allocate-space  -pas  --no-pre-allocate-space  -npas           Whether to pre-allocate space for the file, useful to avoid disk fragmentation. [default: no-pre-allocate-space]                                         │
# >>> │ --use-ram-buffer      -urb  --no-use-ram-buffer      -nurb           Whether to use a RAM buffer to download the file. If True, it will use up to 30% of your total memory to assist in downloading the file, further         │
# >>> │                                                                      speeding up your download and preserving your HDD/SSD. Otherwise it will download and write the file directly to the output file path (very slow).       │
# >>> │                                                                      [default: use-ram-buffer]                                                                                                                                │
# >>> │ --overwrite           -o    --no-overwrite           -no             Overwrite the file if it already exists. Otherwise, a '_1', '_2', etc. suffix will be added. [default: overwrite]                                        │
# >>> │ --expected-hash       -eh                                   TEXT     The expected hash of the downloaded file. If not provided, the hash will not be checked. [default: (No hash check)]                                      │
# >>> │ --hash-type           -ht                                   TEXT     The hash type to use for the hash verification. [default: md5]                                                                                           │
# >>> │ --help                                                               Show this message and exit.                                                                                                                              │
# >>> ╰───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

turbodl [...] https://example.com/file.txt path/to/file
# >>> Downloading "file.txt" ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 25.2/25.2 MB 82.6 MB/s 0:00:00 100%
```

### Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, fork the repository and create a pull request. You can also simply open an issue and describe your ideas or report bugs. **Don't forget to give the project a star if you like it!**

1. Fork the project;
2. Create your feature branch ・ `git checkout -b feature/{feature_name}`;
3. Commit your changes ・ `git commit -m "{commit_message}"`;
4. Push to the branch ・ `git push origin feature/{feature_name}`;
5. Open a pull request, describing the changes you made and wait for a review.
