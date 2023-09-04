from pathlib import Path
from os import remove

from tt_os_abstraction.os_abstraction import env

def on(name): Path(env('temp')).joinpath(name).with_suffix('.tmp').touch()

def off(name): remove(Path(env('temp')).joinpath(name).with_suffix('.tmp'))

def is_on(name): return True if Path(env('temp')).joinpath(name).with_suffix('.tmp').exists() else False
