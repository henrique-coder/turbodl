# Third-party imports
from rich.console import Console
from typer import Argument, Exit, Option, Typer

# Local imports
from turbodl.downloader import TurboDL
from turbodl.exceptions import TurboDLError


app = Typer(no_args_is_help=True, add_completion=False)
console = Console()


@app.command()
def main(
    url: str = Argument(..., help="The download URL to download the file from.", show_default=False),
    output_path: str = Argument(
        None,
        help="The path to save the downloaded file to. If the path is a directory, the file name will be generated from the server response. If the path is a file, the file will be saved with the provided name. If not provided, the file will be saved to the current working directory.",
        show_default="Current working directory",
    ),
    max_connections: str = Option(
        "auto",
        "--max-connections",
        "-mc",
        help="The maximum number of connections to use for downloading the file ('auto' will dynamically calculate the number of connections based on the file size and connection speed and an integer between 1 and 24 will set the number of connections to that value).",
    ),
    connection_speed: float = Option(
        80,
        "--connection-speed",
        "-cs",
        help="Your connection speed in Mbps (megabits per second) (your connection speed will be used to help calculate the optimal number of connections).",
    ),
    show_progress_bars: bool = Option(
        True, "--show-progress-bars/--hide-progress-bars", "-spb/-hpb", help="Show or hide all progress bars."
    ),
    timeout: int = Option(
        None,
        "--timeout",
        "-t",
        help="Timeout in seconds for the download process. Or None for no timeout.",
        show_default="No timeout",
    ),
    pre_allocate_space: bool = Option(
        False,
        "--pre-allocate-space/--no-pre-allocate-space",
        "-pas/-npas",
        help="Whether to pre-allocate space for the file, useful to avoid disk fragmentation.",
    ),
    use_ram_buffer: bool = Option(
        True,
        "--use-ram-buffer/--no-use-ram-buffer",
        "-urb/-nurb",
        help="Whether to use a RAM buffer to download the file. If True, it will use up to 30% of your total memory to assist in downloading the file, further speeding up your download and preserving your HDD/SSD. Otherwise it will download and write the file directly to the output file path (very slow).",
    ),
    overwrite: bool = Option(
        True,
        "--overwrite/--no-overwrite",
        "-o/-no",
        help="Overwrite the file if it already exists. Otherwise, a '_1', '_2', etc. suffix will be added.",
    ),
    expected_hash: str = Option(
        None,
        "--expected-hash",
        "-eh",
        help="The expected hash of the downloaded file. If not provided, the hash will not be checked.",
        show_default="No hash check",
    ),
    hash_type: str = Option("md5", "--hash-type", "-ht", help="The hash type to use for the hash verification."),
) -> None:
    try:
        turbodl = TurboDL(
            max_connections=max_connections,
            connection_speed=connection_speed,
            show_progress_bars=show_progress_bars,
            timeout=timeout,
        )
        turbodl.download(
            url=url,
            output_path=output_path,
            pre_allocate_space=pre_allocate_space,
            use_ram_buffer=use_ram_buffer,
            overwrite=overwrite,
            expected_hash=expected_hash,
            hash_type=hash_type,
        )
    except TurboDLError as e:
        console.print(f"[red]TurbDL (internal) error: {e}")
        raise Exit(1) from e
    except Exception as e:
        console.print(f"[red]Unknown (unhandled) error: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
