from tt_dictionary.dictionary import Dictionary

from time import sleep
from glob import glob
import os
from os.path import join, getctime, abspath
from bs4 import BeautifulSoup as Soup
from pathlib import Path

from tt_google_drive.google_drive import GoogleDrive


def newest_file(folder):
    types = ['*.txt', '*.csv', '*.xml']
    files = []
    for t in types:
        files.extend(glob(join(folder, t)))
    return max(files, key=getctime) if len(files) else None


def wait_for_new_file(folder, event_function):
    newest_before = newest_after = newest_file(folder)
    event_function()
    while newest_before == newest_after:
        sleep(0.1)
        newest_after = newest_file(folder)
    return newest_after


class SoupFromXMLFile:
    def __init__(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as file:
            self.soup = Soup(file, 'xml')


class SoupFromXMLResponse:
    def __init__(self, response):
        self.soup = Soup(response, 'xml')


def print_file_exists(filepath: Path):
    checkmark = u'\N{check mark}'
    if filepath.exists():
        print(f'   {checkmark}   {str(filepath)}')
        return True
    else:
        print(f'   x   {str(filepath)}')
        return False


def read_text_arr(filepath: Path):
    with open(filepath) as text_file:
        lines = [line.splitlines()[0].split(",") for line in text_file]
    return lines


def list_all_files(folder_path):
    file_list = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            full_path = join(root, file)
            file_list.append(full_path)
    return file_list

class FileTree(Dictionary):


    def find_keys(self, target_key, target_value=None, _found_keys=None, _path=None):
        """
        retrieve key/value pairs that match the target_key
        :param target_key: key to be found
        :param target_value: value of found key
        :param _found_keys: list of found items, passed to next recursion
        :param _path: string of dictionary names
        :return _found_keys: list of found item tuples (key, value)
        """
        if _found_keys is None:
            _found_keys = []

        for key, value in self.items():
            if key == target_key:
                if target_value is not None:
                    if value == target_value:
                        _found_keys.append((f'{_path}/{key}' if _path else {key}, value))
                else:
                    _found_keys.append((f'{_path}/{key}' if _path else {key}, value))
            if isinstance(value, FileTree):
                _path = f'[{_path}][{key}]'
                value.find_keys(target_key, target_value, _found_keys)
        return _found_keys


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class OSFileTree(FileTree):
    """
    create a Dictionary representing a folder-file hierarchy from a Windows or Mac drive
    :param start: path to folder hierarchy; none uses entire drive (root)
    """
    # root_path = abspath('/')

    def __init__(self, *args, start_path: Path = abspath('/'), **kwargs):
        super().__init__(*args, **kwargs)

        if not 'json_source' in kwargs:

            print("🚀 building file tree dictionary")
            for path, dirs, files in os.walk(start_path):
                name = Path(path).name
                path_parts = Path(path).relative_to(start_path.parent).parts
                indent = " " * (len(path_parts)-1)

                base = self
                for i in range(len(path_parts)-1):
                    base = base[path_parts[i]]

                base[name] = FileTree({'path': path, 'type': 'folder'})

                for file in files:
                    base[name][file] = FileTree({'path': path, 'name': file, 'size': os.path.getsize(Path(path).joinpath(file)), 'type': Path(file).suffix})

                print(f"{indent}📁 {name}: {len(dirs)} folders, {len(files)} files")


class GoogleDriveTree(FileTree):
    """
    create a Dictionary representing a folder-file hierarchy from the Google Drive API
    :param start: path to folder hierarchy; none uses entire drive (root)
    """

    def __init__(self, *args, start_path: str = '/', **kwargs):
        super().__init__(*args, **kwargs)

        drive = GoogleDrive()

        if not 'json_source' in kwargs:

            print("🚀 building drive tree dictionary")

            google_drive_id = drive.get_path_id(start_path)
            for path, google_drive_id, dirs, files in drive.walk_drive(google_drive_id):
                path_parts = [f.strip() for f in path.split('/') if f.strip()]
                name = path_parts[-1]
                indent = " " * (len(path_parts)-1)

                base = self
                for i in range(len(path_parts)-1):
                    base = base[path_parts[i]]

                base[name] = FileTree({'id': google_drive_id, 'type': 'folder'})

                for file in files:
                    base[name][file[0]] = FileTree({'name': file[0], 'id': file[1], 'size': file[2], 'type': 'file'})

                print(f"{indent}📁 {name}: {len(dirs)} folders, {len(files)} files")

