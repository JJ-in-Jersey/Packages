from glob import glob
from os.path import join, getctime

class FileUtilities:

    @staticmethod
    def newest_file(folder):
        types = ['*.txt', '*.csv']
        files = []
        for t in types: files.extend(glob(join(folder, t)))
        return max(files, key=getctime) if len(files) else None

    def __init__(self):
        pass