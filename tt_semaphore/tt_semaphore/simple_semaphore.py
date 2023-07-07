from pathlib import Path
from os import environ, remove
import platform

if platform.system() == 'Windows':
    TEMP = environ['TEMP']
elif platform.system() == 'Darwin':
    TEMP = environ['TMPDIR']

def on(name): Path(TEMP).joinpath(name).with_suffix('.tmp').touch()

def off(name): remove(Path(TEMP).joinpath(name).with_suffix('.tmp'))

def is_on(name): return True if Path(TEMP).joinpath(name).with_suffix('.tmp').exists() else False