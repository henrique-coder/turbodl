## TurboDL

![PyPI - Version](https://img.shields.io/pypi/v/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Downloads](https://img.shields.io/pypi/dm/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Code Style](https://img.shields.io/badge/code%20style-ruff-blue?style=flat&logo=ruff&logoColor=blue&color=blue&link=https://github.com/astral-sh/ruff)
![PyPI - Format](https://img.shields.io/pypi/format/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Python Compatible Versions](https://img.shields.io/pypi/pyversions/turbodl?style=flat&logo=python&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)

TurboDL ia an extremely smart, fast and efficient download manager with several automations.

- Uses HTTP/2 protocol to download files.
- Built-in sophisticated download acceleration technique.
- Retry failed requests efficiently.
- Automatically detects file information before download.
- Automatically handles redirects.
- Supports post-download hash verification.
- Automatically uses RAM buffer to speed up downloads and reduce disk I/O.
- Accurately displays a beautiful progress bar.

<br>

#### Installation (from [PyPI](https://pypi.org/project/turbodl))

```bash
pip install -U turbodl  # Install the latest version of TurboDL
```

### Example Usage

#### Inside a Python script

```python
from turbodl import TurboDL


turbodl = TurboDL(
    max_connections='auto',
    connection_speed=80,
    show_progress_bars=True,
    custom_headers=None,
    timeout=None
)

turbodl.download(
    url='https://example.com/file.txt',
    output_path='path/to/file',
    expected_hash='0a1b2c3d4e5f6g7h8i9j',  # Or None if you don't want to check the hash
    hash_type='md5'
    pre_allocate_space=False,
    use_ram_buffer=True,
)
# >>> file.txt ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 35.6/35.6 kB 36.2 MB/s 0:00:00 100%

# All functions are documented and have detailed typings, use your development IDE to learn more.

```

#### From the command line

```bash
turbodl --help
# >>> ╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
# >>> │ *    url              TEXT           The download URL to download the file from. [default: None] [required]                                                                                                                  │
# >>> │      output_path      [OUTPUT_PATH]  The path to save the downloaded file to. If the path is a directory, the file name will be generated from the server response. If the path is a file, the file will be saved with the   │
# >>> │                                      provided name. If not provided, the file will be saved to the current working directory. (default: Path.cwd())                                                                          │
# >>> │                                      [default: None]                                                                                                                                                                         │
# >>> ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
# >>> ╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
# >>> │ --max-connections     -mc                               INTEGER  The maximum number of connections to use for downloading the file (default: 'auto'). [default: None]                                                        │
# >>> │ --connection-speed    -cs                               FLOAT    Your connection speed in Mbps (default: 80). [default: None]                                                                                                │
# >>> │ --overwrite           -o    --no-overwrite        -no            Overwrite the file if it already exists. Otherwise, a "_1", "_2", etc. suffix will be added. [default: overwrite]                                           │
# >>> │ --show-progress-bars  -spb  --hide-progress-bars  -hpb           Show or hide all progress bars. [default: show-progress-bars]                                                                                               │
# >>> │ --timeout             -t                                INTEGER  Timeout in seconds for the download process. Or None for no timeout. [default: None]                                                                        │
# >>> │ --help                                                           Show this message and exit.                                                                                                                                 │
# >>> ╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

turbodl https://example.com/file.txt [...] path/to/file  # Tip: use -cs argument to set your connection speed in Mbps and accelerate the download
# >>> file.txt ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 35.6/35.6 kB 36.2 MB/s 0:00:00 100%
```

### Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, fork the repository and create a pull request. You can also simply open an issue and describe your ideas or report bugs. **Don't forget to give the project a star if you like it!**

1. Fork the project;
2. Create your feature branch ・ `git checkout -b feature/{feature_name}`;
3. Commit your changes ・ `git commit -m "{commit_message}"`;
4. Push to the branch ・ `git push origin feature/{feature_name}`;
5. Open a pull request, describing the changes you made and wait for a review.

### Disclaimer

Please note that downloading copyrighted content from some services may be illegal in your country. This tool is designed for educational purposes only. Use at your own risk.
