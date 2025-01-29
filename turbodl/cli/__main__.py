# Third-party imports
from httpx import get
from rich.console import Console
from typer import Argument, Exit, Option, Typer

# Local imports
from turbodl import __version__
from turbodl.downloader import TurboDL
from turbodl.exceptions import TurboDLError


app = Typer(
    no_args_is_help=True, add_completion=False, context_settings={"help_option_names": ["-h", "--help"]}, rich_markup_mode="rich"
)
console = Console()


def process_buffer_options(
    auto: bool, use: bool, disable: bool, hide_progress: bool, preallocate: bool, no_overwrite: bool
) -> tuple[str | bool, bool, bool, bool]:
    if auto:
        ram_buffer = "auto"
    elif use:
        ram_buffer = True
    elif disable:
        ram_buffer = False
    else:
        ram_buffer = "auto"

    return ram_buffer, not hide_progress, preallocate, not no_overwrite


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold white]TurboDL (turbodl) [bold green]{__version__}[/]")
        raise Exit()


def check_for_updates() -> None:
    try:
        r = get("https://api.github.com/repos/henrique-coder/turbodl/releases/latest", follow_redirects=False)

        if r.status_code == 200:
            latest_version = r.json()["tag_name"].replace("v", "")

            if latest_version > __version__:
                console.print(
                    f"[yellow]Update available![/] Current version: [red]{__version__}[/] → Latest version: [green]{latest_version}[/]"
                )
                console.print("\nTo update, run: [bold cyan]pip install -U turbodl[/]")
            else:
                console.print(f"[green]TurboDL is up to date![/] Current version: [bold]{__version__}[/]")
        else:
            console.print("[red]Failed to check for updates: Could not reach GitHub API[/]")
    except Exception as e:
        console.print(f"[red]Failed to check for updates: {str(e)}[/]")
        raise Exit(1) from e


@app.callback(invoke_without_command=True)
def callback(
    version: bool = Option(None, "--version", "-v", help="Show version and exit.", callback=version_callback, is_eager=True),
) -> None:
    """[bold cyan]TurboDL[/] is an extremely smart, fast, and efficient download manager with several automations.

    [bold yellow]\nExamples:[/]\n   Download a file:\n   [dim]$ turbodl download https://example.com/file.zip\n\n   Download a file to a specific path:\n   [dim]$ turbodl download https://example.com/file.zip /path/to/file[/]
    [bold yellow]\nMore Help:[/]\n   For detailed download options, use:\n   [dim]$ turbodl download --help[/]"""


@app.command()
def check() -> None:
    """
    Check for available updates.
    """

    check_for_updates()


@app.command()
def download(
    url: str = Argument(..., help="Download URL."),
    output_path: str = Argument(
        None, help="Destination path. If directory, filename is derived from server response.", show_default="Current directory"
    ),
    max_connections: str = Option("auto", "--max-connections", "-mc", help="Max connections: 'auto' or integer (1-24)."),
    connection_speed: float = Option(80, "--connection-speed", "-cs", help="Connection speed in Mbps for optimal connections."),
    hide_progress_bars: bool = Option(
        False, "--hide-progress-bars", "-hpb", help="Hide progress bars (shown by default).", is_flag=True
    ),
    save_logfile: bool = Option(False, "--save-logfile", "-sl", help="Save log messages to a file.", is_flag=True),
    allocate_space: bool = Option(
        False, "--pre-allocate-space", "-pas", help="Pre-allocate disk space before downloading.", is_flag=True
    ),
    auto_ram_buffer: bool = Option(
        False, "--auto-ram-buffer", "-arb", help="Use RAM buffer automatically if path isn't RAM dir (default).", is_flag=True
    ),
    use_ram_buffer: bool = Option(False, "--use-ram-buffer", "-urb", help="Always use RAM buffer.", is_flag=True),
    no_ram_buffer: bool = Option(False, "--no-ram-buffer", "-nrb", help="Never use RAM buffer.", is_flag=True),
    no_overwrite: bool = Option(
        False, "--no-overwrite", "-no", help="Don't overwrite existing files (overwrite by default).", is_flag=True
    ),
    timeout: int = Option(None, "--timeout", "-t", help="Download timeout in seconds."),
    expected_hash: str = Option(None, "--expected-hash", "-eh", help="Expected file hash for verification."),
    hash_type: str = Option("md5", "--hash-type", "-ht", help="Hash algorithm for verification."),
) -> None:
    """
    Download a file from the provided URL to the specified output path (with a lot of options)
    """

    ram_buffer_value, show_progress_bars, pre_allocate_space, overwrite = process_buffer_options(
        auto_ram_buffer, use_ram_buffer, no_ram_buffer, hide_progress_bars, allocate_space, no_overwrite
    )

    try:
        turbodl = TurboDL(
            max_connections=max_connections,
            connection_speed=connection_speed,
            show_progress_bars=show_progress_bars,
            save_logfile=save_logfile,
        )
        turbodl.download(
            url=url,
            output_path=output_path,
            pre_allocate_space=pre_allocate_space,
            use_ram_buffer=ram_buffer_value,
            overwrite=overwrite,
            timeout=timeout,
            expected_hash=expected_hash,
            hash_type=hash_type,
        )
    except TurboDLError as e:
        console.print(f"[red]TurboDL (internal) error: {e}")
        raise Exit(1) from e
    except Exception as e:
        console.print(f"[red]Unknown (unhandled) error: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
