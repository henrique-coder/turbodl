# Built-in imports
from pathlib import Path

# Third-party imports
from typer import Typer, Argument, Option, Exit
from rich.console import Console

# Local imports
from ..downloader import TurboDL
from ..exceptions import DownloadError, RequestError, TurboDLError


app = Typer()
console = Console()


@app.command()
def main(
    url: str = Argument(..., help='The download URL to download the file from.'),
    output_path: str = Argument(
        None,
        help='The path to save the downloaded file to. If the path is a directory, the file name will be generated from the server response. If the path is a file, the file will be saved with the provided name. If not provided, the file will be saved to the current working directory. (default: Path.cwd())',
    ),
    max_connections: int = Option(
        None,
        '--max-connections',
        '-mc',
        help='The maximum number of connections to use for downloading the file. (default: auto)',
    ),
    connection_speed: float = Option(None, '--connection-speed', '-cs', help='The connection speed in Mbps. (default: 80)'),
    overwrite: bool = Option(
        None,
        '--overwrite/--no-overwrite',
        '-o/-no',
        help='Overwrite the file if it already exists. Otherwise, a "_1", "_2", etc. suffix will be added. (default: True)',
    ),
    show_progress: bool = Option(
        None, '--show-progress/--hide-progress', '-sp/-hp', help='Show or hide the download progress bar. (default: True)'
    ),
    timeout: int = Option(
        None, '--timeout', '-t', help='Timeout in seconds for the download process. Or None for no timeout. (default: None)'
    ),
) -> None:
    try:
        turbodl = TurboDL(
            max_connections='auto' if max_connections is None else max_connections,
            connection_speed=80 if connection_speed is None else connection_speed,
            overwrite=True if overwrite is None else overwrite,
            show_progress_bar=True if show_progress is None else show_progress,
            timeout=timeout,
        )

        if not output_path:
            output_path = Path(Path.cwd(), Path(url).name)

        turbodl.download(url=url, output_path=output_path)

    except (DownloadError, RequestError, TurboDLError) as e:
        console.print(f'[red]Error: {str(e)}')
        raise Exit(1)


if __name__ == '__main__':
    app()
