# Built-in mobules
from os import PathLike
from pathlib import Path
from shutil import which
from subprocess import DEVNULL, CalledProcessError, run
from typing import Literal

# Local modules
from .exceptions import FFmpegNotFoundError, MergeError


class Merger:
    """A class for merging multiple audio and video streams into a single file."""

    def __init__(self, logging: bool = False) -> None:
        """
        Initialize the Merger class with the required settings for merging audio and video streams.

        Args:
            logging: Enable or disable FFmpeg logging. Defaults to False.
        """

        self._logging = logging

    def merge(
        self,
        video_path: str | PathLike,
        audio_path: str | PathLike,
        output_path: str | PathLike,
        ffmpeg_path: str | PathLike | Literal["local"] = "local",
    ) -> None:
        """
        Merge the video and audio streams into a single file.

        Args:
            video_path: The path to the video file to merge.
            audio_path: The path to the audio file to merge.
            output_path: The path to save the output file to.
            ffmpeg_path: The path to the FFmpeg executable. If 'local', the FFmpeg executable will be searched in the PATH environment variable. Defaults to 'local'.

        Raises:
            FFmpegNotFoundError: If the FFmpeg executable was not found.
            MergeError: If an error occurs while merging the files.
        """

        video_path = Path(video_path).resolve()
        audio_path = Path(audio_path).resolve()
        output_path = Path(output_path).resolve()

        if ffmpeg_path == "local":
            found_ffmpeg_binary = which("ffmpeg")

            if found_ffmpeg_binary:
                ffmpeg_path = Path(found_ffmpeg_binary)
            else:
                raise FFmpegNotFoundError(
                    "The FFmpeg executable was not found. Please provide the path to the FFmpeg executable."
                )
        else:
            ffmpeg_path = Path(ffmpeg_path).resolve()

        stdout = None if self._logging else DEVNULL
        stderr = None if self._logging else DEVNULL

        try:
            run(
                [
                    ffmpeg_path.as_posix(),
                    "-y",
                    "-hide_banner",
                    "-i",
                    video_path.as_posix(),
                    "-i",
                    audio_path.as_posix(),
                    "-c",
                    "copy",
                    "-map",
                    "0:v",
                    "-map",
                    "1:a",
                    output_path.as_posix(),
                ],
                check=True,
                stdout=stdout,
                stderr=stderr,
            )
        except CalledProcessError as e:
            raise MergeError(
                f'Error occurred while merging files: "{video_path.as_posix()}" and "{audio_path.as_posix()}" to "{output_path.as_posix()}".'
            ) from e
