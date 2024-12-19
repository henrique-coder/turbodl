## TurboDL

![PyPI - Version](https://img.shields.io/pypi/v/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Downloads](https://img.shields.io/pypi/dm/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Code Style](https://img.shields.io/badge/code%20style-ruff-blue?style=flat&logo=ruff&logoColor=blue&color=blue&link=https://github.com/astral-sh/ruff)
![PyPI - Format](https://img.shields.io/pypi/format/turbodl?style=flat&logo=pypi&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)
![PyPI - Python Compatible Versions](https://img.shields.io/pypi/pyversions/turbodl?style=flat&logo=python&logoColor=blue&color=blue&link=https://pypi.org/project/turbodl)

TurboDL is an extremely smart and efficient download manager for various cases.

- Built-in download acceleration.
- Uses your connection speed to download even more efficiently.
- Retries failed requests.
- Automatically detects the file type, name, extension, and size.
- Automatically handles redirects.
- Shows a fancy and precise progress bar.

<br>

#### Installation (from [PyPI](https://pypi.org/project/turbodl))

```bash
pip install -U turbodl  # Install the latest version of TurboDL
```

### Example Usage

```python
from turbodl import TurboDL
from pathlib import Path  # Optional


turbodl = TurboDL(
    max_connections='auto',
    connection_speed=80,
    show_progress_bar=True,
    custom_headers=None,
    timeout=None
)

turbodl.download(
    url='https://example.com/file',
    output_path=Path.cwd()
)
# >>> Downloading a {mime} file ({mime/type}) ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 35.6/35.6 kB 81.2 MB/s 0:00:00

# All functions are documented and have detailed typings, use your development IDE to learn more.

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
