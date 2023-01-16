from pathlib import Path
from os import environ, remove

class Simple_Semaphore:

    @staticmethod
    def on(name): Path(environ['TEMP']).joinpath(name).with_suffix('.tmp').touch()

    @staticmethod
    def off(name): remove(Path(environ['TEMP']).joinpath(name).with_suffix('.tmp'))

    @staticmethod
    def is_on(name): return True if Path(environ['TEMP']).joinpath(name).with_suffix('.tmp').exists() else False

    def __init__(self):
        pass
