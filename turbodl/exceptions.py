class TurboDLError(Exception):
    """Base class for all TurboDL exceptions."""

    pass


class DownloadError(TurboDLError):
    """Exception raised when an error occurs while downloading a file."""

    pass


class HashVerificationError(TurboDLError):
    """Exception raised when the hash of the downloaded file does not match the expected hash."""

    pass


class InsufficientSpaceError(TurboDLError):
    """Exception raised when there is not enough space to download the file."""

    pass


class RequestError(TurboDLError):
    """Exception raised when an error occurs while making a request."""

    pass
