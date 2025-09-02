# errors.py
class SandboxError(Exception):
    """Base exception for all sandbox related errors."""

    def __init__(self, message: str = "sandbox error") -> None:
        """Initialize the SandboxError."""
        super().__init__(message)


class BackendError(SandboxError):
    """Raised when Backend operation fail   """

class BackendNotAvailable(SandboxError):
    """" Raised when Backend not available"""

class ImageNotFoundError(SandboxError):
    """Raised when the image is not found."""

    def __init__(self, image: str) -> None:
        """Initialize the ImageNotFoundError."""
        super().__init__(f"Image {image} not found")