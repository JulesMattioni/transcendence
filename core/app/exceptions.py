class FileServiceError(Exception):
    """
    Base class for all business errors raised by the file service.
    """


class FileNotFoundError(FileServiceError):
    """
    Raised when a requested file does not exist.
    """


class FileAccessDeniedError(FileServiceError):
    """
    Raised when the current user is not allowed to act on a file.
    """
