from pathlib import Path
from os import environ, remove

def on(name): Path(environ['TEMP']).joinpath(name).with_suffix('.tmp').touch()

def off(name): remove(Path(environ['TEMP']).joinpath(name).with_suffix('.tmp'))

def is_on(name): return True if Path(environ['TEMP']).joinpath(name).with_suffix('.tmp').exists() else False
