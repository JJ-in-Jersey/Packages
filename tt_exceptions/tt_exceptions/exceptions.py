class NonMonotonic(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)


class DataNotAvailable(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)


class DataMissing(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)


class DuplicateValues(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)


class LengthMismatch(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)


class EmptyResponse(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)


class SplineCSVFailed(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(message)


class FileIsEmpty(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(message)


class FileSampleIsEmpty(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(message)


class GoogleAuthenticationFailure(Exception):
    def __init__(self, message: str = None):
        print(f'\n1. Go to the Google CloudConsole: https://console.cloud.google.com')
        print(f'   Make sure you select the correct project where your Google Drive API was enabled.')
        print(f'   You can do this from the project selector dropdown at the top of the page. Upper left: hamburger, Google Cloud logo, 3 dots box.')
        print(f'\n2. Navigate to API & Services > Credentials: Select the Quick Access Box "API APIs & Services"')
        print(f'   On left-hand side menu, select the horizontal 🗝 icon')
        print(f'   [If necessary, delete old credentials. Select the client id from OAuth 2.0 Client IDs list. At the top of the menu, select Delete.]')
        print(f'   At the top of the menu, select Create credentials, then select Outh Client ID')
        print(f'   For Application type, select Desktop app. Enter a OAuth 2.0 Client name for reference. Select Create.')
        print(f'   From the pop-up menu, download the credentials json file and rename it "client_secret.json"')
        print(f'   Move client_secret.json from Downloads to the executable folder.')
        print(f'\n')
        self.message = message
        super().__init__(self.message)


class GoogleServiceBuildFailure(Exception):
    def __init__(self, message: str = None):
        self.message = message
        super().__init__(self.message)
