from time import sleep
from glob import glob
import os
from os.path import join, getctime
from bs4 import BeautifulSoup as Soup
from pathlib import Path
import json


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
        with open(filepath, 'r') as f:
            content = f.read()
        self.tree = Soup(f, 'lxml')


class SoupFromXMLResponse:
    def __init__(self, response):
        self.tree = Soup(response, 'lxml')


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