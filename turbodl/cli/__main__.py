# Third-party modules
from httpx import get
from rich.console import Console
from typer import Argument, Exit, Option, Typer

# Local imports
from turbodl import TurboDL, __version__
from turbodl.exceptions import TurboDLError


app = Typer(
    no_args_is_help=True, add_completion=False, context_settings={"help_option_names": ["-h", "--help"]}, rich_markup_mode="rich"
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold white]TurboDL (turbodl) [bold green]{__version__}[/]")
        raise Exit()


def check_for_updates() -> None:
    try:
        r = get("https://api.github.com/repos/henrique-coder/turbodl/releases/latest", follow_redirects=False)
        if r.status_code != 200:
            console.print("[red]Failed to check for updates: Could not reach GitHub API[/]")
            return

        latest_version = r.json()["tag_name"].replace("v", "")
        if latest_version > __version__:
            console.print(
                f"[yellow]Update available![/] Current version: [red]{__version__}[/] → Latest version: [green]{latest_version}[/]\n"
                "\nTo update, run: [bold cyan]pip install -U turbodl[/]"
            )
        else:
            console.print(f"[green]TurboDL is up to date![/] Current version: [bold]{__version__}[/]")
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
    max_connections: str = Option("auto", "--max-connections", "-mc", help="Max connections: 'auto' or integer (1-32)."),
    connection_speed_mbps: int = Option(
        80, "--connection-speed", "-cs", help="Connection speed in Mbps for optimal connections."
    ),
    hide_progress_bar: bool = Option(
        False, "--hide-progress-bar", "-hpb", help="Hide progress bar (shown by default).", is_flag=True
    ),
    save_log_file: bool = Option(
        False, "--save-logfile", "-sl", help="Save a turbodl-download.log file to the download directory.", is_flag=True
    ),
    allocate_space: bool = Option(
        False, "--pre-allocate-space", "-pas", help="Pre-allocate disk space before downloading.", is_flag=True
    ),
    auto_ram_buffer: bool = Option(
        False, "--auto-ram-buffer", "-arb", help="Use RAM buffer automatically if path isn't RAM dir (default).", is_flag=True
    ),
    enable_ram_buffer: bool = Option(False, "--enable-ram-buffer", "-erb", help="Always use RAM buffer.", is_flag=True),
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

    # Process max_connections
    try:
        max_conn = int(max_connections) if max_connections != "auto" else "auto"
    except ValueError as e:
        console.print("[red]Error: max-connections must be 'auto' or an integer[/]")
        raise Exit(1) from e

    # Process RAM buffer options
    ram_buffer = "auto"
    if enable_ram_buffer:
        ram_buffer = True
    elif no_ram_buffer:
        ram_buffer = False
    elif auto_ram_buffer:
        ram_buffer = "auto"

    try:
        turbodl = TurboDL(
            max_connections=max_conn,
            connection_speed_mbps=connection_speed_mbps,
            show_progress_bar=not hide_progress_bar,
            save_log_file=save_log_file,
        )
        turbodl.download(
            url=url,
            output_path=output_path,
            pre_allocate_space=allocate_space,
            enable_ram_buffer=ram_buffer,
            overwrite=not no_overwrite,
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
