from glob import glob
from os.path import join, getctime
from pathlib import Path
from os import makedirs

class FileTools:

    @staticmethod
    def newest_file(folder):
        types = ['*.txt', '*.csv']
        files = []
        for t in types: files.extend(glob(join(folder, t)))
        return max(files, key=getctime) if len(files) else None

    @staticmethod
    def make_folder(parent, child):
        if not isinstance(parent, Path): raise TypeError
        path = parent.joinpath(child)
        makedirs(path, exist_ok=True)
        return path

    def __init__(self):
        pass
