from glob import glob
from os.path import join, getctime
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
        if isinstance(parent, str): parent = Path(parent)
        path = parent.joinpath(child)
        makedirs(path, exist_ok=True)
        return path

    def __init__(self):
        pass
