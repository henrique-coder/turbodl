class TurboDLError(Exception):
    """Base class for all TurboDL exceptions."""

    pass


class DownloadError(TurboDLError):
    """Exception raised when an error occurs while downloading a file."""

    pass


class RequestError(TurboDLError):
    """Exception raised when an error occurs while making a request."""

    pass
