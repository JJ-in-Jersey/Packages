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
    """
    create a Dictionary representing a folder-file hierarchy from a Windows or Mac drive
    :param start: path to folder hierarchy; none uses entire drive (root)
    """
    root_path = abspath('/')

    def __init__(self, start: Path = None, *args):
        super().__init__(*args)

        start = FileTree.root_path if start is None else start

        current_dict = self
        dict_path = ''

        print("🚀 building file tree dictionary")
        for current_folder_path, folder_names, file_names in os.walk(self.start):
            current_folder_path = Path(current_folder_path)
            dict_path = dict_path + '/' + current_folder_path.name
            print(dict_path)
            indent = " " * (len(current_folder_path.parts) - len(start.parts))
            current_dict[current_folder_path.name] = Dictionary({'path': current_folder_path})
            for folder in folder_names:
                folder_path = current_folder_path.joinpath(folder)
                current_dict[current_folder_path.name][folder] = Dictionary({'name': folder_path})
            for file in file_names:
                file_path = current_folder_path.joinpath(file)
                current_dict[current_folder_path.name][file] = Dictionary({'name': file_path, 'file_size': os.path.getsize(file_path), 'type': file_path.suffix})
            current_dict = current_dict[current_folder_path.name]
            print(f"{indent}📁 {current_folder_path.name}: {len(folder_names)} folders, {len(file_names)} files)")


class GoogleDriveTree(Dictionary):
    """
    create a Dictionary representing a folder-file hierarchy from the Google Drive API
    :param start: path to folder hierarchy; none uses entire drive (root)
    """


    def __init__(self, start_path: str = '/', *args):
        super().__init__(*args)

        drive = GoogleDrive()

        print("🚀 building drive tree dictionary")

        id = drive.get_path_id(start_path)
        for depth, path, id, dirs, files in drive.walk_drive(id):
            indent = " " * depth
            path_parts = [f.strip() for f in path.split('/') if f.strip()]
            name = path_parts[-1]

            base = self
            for i in range(len(path_parts)-1):
                base = base[path_parts[i]]

            base[name] = Dictionary({'id': id, 'type': 'folder'})

            for file in files:
                base[name][file[0]] = Dictionary({'name': file[0], 'id': file[1], 'type': 'file'})

            print(f"{indent}📁 {name}: {len(dirs)} folders, {len(files)} files")