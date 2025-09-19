import os
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from tt_exceptions.exceptions import GoogleAuthenticationFailure, GoogleServiceBuildFailure

# Define the scopes required for Google Drive API access.
# 'https://www.googleapis.com/auth/drive' gives full access to Google Drive.
# For more restricted access, you might
# use 'https://www.googleapis.com/auth/drive.file'
# which only allows access to files created or opened by the app.
DRIVE_JSON = Path('google_drive.json')
CSV_PREFIX = 'https://drive.google.com/file/d/'
CSV_SUFFIX = '/view?usp=drive_link'
FOLDER_MIMETYPE = 'application/vnd.google-apps.folder'
PNG_MIMETYPE = 'image/png'
FILE_MIMETYPE = 'application/vnd.google-apps.file'
IMAGES_FOLDER = 'images 3.0'
GOOGLE_URLS_CSV = 'google_urls.csv'

class GoogleDrive:

    scopes = ['https://www.googleapis.com/auth/drive']
    client_secret = 'client_secret.json'
    token = 'token.json'
    folder_mimetype = 'application/vnd.google-apps.folder'
    png_mimetype = 'image/png'
    file_mimetype = 'application/vnd.google-apps.file'

    @staticmethod
    def get_drive_credentials():
        """
        It checks for existing credentials, refreshes them if expired,
        or initiates a new OAuth 2.0 flow if no credentials are found.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        try:
            if os.path.exists(GoogleDrive.token):
                creds = Credentials.from_authorized_user_file(GoogleDrive.token, GoogleDrive.scopes)
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    # The client_secrets.json file contains your OAuth 2.0 client ID and client secret.
                    # You download this from the Google Cloud Console.
                    if Path(GoogleDrive.client_secret).exists():
                        flow = InstalledAppFlow.from_client_secrets_file(
                            GoogleDrive.client_secret, GoogleDrive.scopes)
                        creds = flow.run_local_server(port=0)
                    else:
                        raise GoogleAuthenticationFailure('No credentials file found')

                # Save the credentials for the next run
                with open(GoogleDrive.token, 'w') as token:
                    token.write(creds.to_json())
            return creds
        except GoogleAuthenticationFailure as error:
            print(f"An error occurred while getting drive credentials: {error}")

    @staticmethod
    def get_drive_service(creds):
        """
        returns the Google Drive API service object
        """
        try:
            service = build('drive', 'v3', credentials=creds)
            print("Google Drive service built successfully.")
            return service
        except GoogleServiceBuildFailure as error:
            print(f"An error occurred while building the Drive service: {error}")
            return None


    def walk_drive(self, folder_id: str = 'root', _drive_path: str = '' ):
        """
        A generator that mimics os.walk for Google Drive. Yields a tuple ((folder, id), [(subfolder, id)...], [(file, id)...])
        for each directory in the tree.
        :param folder_id: id of the folder to walk
        :param _drive_path: path to folder being walked, internal only
        """
        try:
            # Get the name of the current folder
            if folder_id == 'root':
                folder_name = 'root'
            else:
                folder_metadata = self.service.files().get(fileId=folder_id, fields='name').execute()
                folder_name = folder_metadata.get('name')

            _drive_path = f'{_drive_path}/{folder_name}'

            all_items = []
            next_page_token = None
            while True:
                # List contents of the current folder with pagination
                results = self.service.files().list(
                    q=f"'{folder_id}' in parents and trashed = false",
                    fields="nextPageToken, files(id, name, mimeType, size)",
                    pageSize=1000,
                    pageToken=next_page_token
                ).execute()

                all_items.extend(results.get('files', []))
                next_page_token = results.get('nextPageToken')
                if not next_page_token:
                    break


            # Separate directories and files
            dirs = [(item['name'], item['id']) for item in all_items if
                    item['mimeType'] == 'application/vnd.google-apps.folder']
            files = [(item['name'], item['id'], item['size']) for item in all_items if
                     item['mimeType'] != 'application/vnd.google-apps.folder']

            # Yield the current directory and its contents
            # noinspection PyRedundantParentheses
            yield (_drive_path, folder_id, dirs, files)

            # Recursively walk subdirectories
            for d in dirs:
                yield from self.walk_drive(d[1], _drive_path)

        except HttpError as error:
            print(f"An HTTP error occurred: {error}")
            return


    def get_name(self, file_id: str ):
        """
        returns item name for a given file_id
        :param file_id: file_id of the item
        """
        try:
            folder_metadata = self.service.files().get(fileId=file_id, fields='name').execute()
            return folder_metadata.get('name')
        except HttpError as error:
            print(f"An HTTP error occurred: {error}")
            return None


    def get_path_id(self, folder_path: str = None):
        """
        returns the id of the folder at the end of a '/' delimited string
        """
        if folder_path:
            folders = [f.strip() for f in folder_path.split('/') if f.strip()]
            if not len(folders):
                _id = 'root'
            else:
                _id = self.get_folder_id(folders[0])
                for folder in folders[1:]:
                    _id = self.get_folder_id(folder, _id)
        else:
            _id = 'root'
        return _id


    def get_folder_id(self, folder_name, parent_id='root'):
        """
        returns the ID of a folder by its name, optionally within a parent folder
        :params service: authenticated Google Drive API service object
        :params folder_name (str): name of the folder to find
        :params parent_id (str, optional): ID of the parent folder. Defaults to 'root'
        """
        try:
            query = (f"name = '{folder_name}' and "
                     f"mimeType = 'application/vnd.google-apps.folder' and "
                     f"trashed = false and "
                     f"'{parent_id}' in parents")
            results = self.service.files().list(q=query, fields="nextPageToken, files(id, name)", pageSize=1, ).execute()
            items = results.get("files", [])

            if items:
                folder_id = items[0]["id"]
                return folder_id
            else:
                print(f"No folder named '{folder_name}' found.")
                return None

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None


    def delete_file(self, file_id: str):
        """
        Deletes a file from Google Drive.
        :param file_id: The ID of the file to delete.
        """
        file_name = self.get_name(file_id)
        print(f'deleting File ({file_name}: {file_id})')
        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f"File ({file_name}: {file_id}) deleted successfully.")
        except HttpError as error:
            print(f"An error occurred while deleting file: {error}")


    def get_folder_items(self, parent_id=None):
        """
        Retrieves files and folders for a given parent ID.
        If parent_id is None, it gets items from My Drive (root).
        """
        items = []
        token = None
        # Query to get children of a specific folder ID or 'root' (My Drive)
        # and exclude trashed items.
        query = f"'{parent_id}' in parents and trashed = false" if parent_id else "'root' in parents and trashed = false"

        while True:
            try:
                # Request only the fields essential for building the tree: id, name, mimeType, parents
                response = self.service.files().list(q=query, spaces='drive',
                                                     fields='nextPageToken, files(id, name, size, mimeType)',
                                                     pageToken=token).execute()
                items.extend(response.get('files', []))
                token = response.get('nextPageToken', None)
                if not token:
                    break  # No more pages, exit loop
            except HttpError as error:
                print(f'An error occurred while listing files: {error}')
                break  # Exit on error
        return items


    def __init__(self):
        try:
            cred = self.get_drive_credentials()
            self.service = self.get_drive_service(cred)

        except RefreshError:
            raise GoogleAuthenticationFailure

