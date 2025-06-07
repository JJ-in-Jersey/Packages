class NonMonotonic(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DataNotAvailable(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DataMissing(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DuplicateValues(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EmptyDataframe(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class SplineCSVFailed(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class FileIsEmpty(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class FileSampleIsEmpty(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class LengthMismatch(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
