from pathlib import Path
from os import environ, remove
import platform

if platform.system() == 'Windows':
    temp = environ['TEMP']
elif platform.system() == 'Darwin':
    temp = environ['TMPDIR']

def on(name): Path(temp).joinpath(name).with_suffix('.tmp').touch()

def off(name): remove(Path(temp).joinpath(name).with_suffix('.tmp'))

def is_on(name): return True if Path(temp).joinpath(name).with_suffix('.tmp').exists() else False
