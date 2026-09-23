class DomainError(Exception):
    """Base class for errors whose message is safe to show to the user as-is."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EmptyFileError(DomainError):
    pass


class FileTooLargeError(DomainError):
    pass


class UnsupportedFileTypeError(DomainError):
    pass


class AssetNotFoundError(DomainError):
    pass


class BlankQueryError(DomainError):
    pass


class AiAnswerCutOffError(DomainError):
    """The model hit its output token limit, so the JSON answer is unusable."""

    def __init__(self) -> None:
        super().__init__("The AI answer was cut off. Try a smaller file.")
