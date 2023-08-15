from pathlib import Path
from os import remove

from tt_os_tools.os_tools import Temp


def on(name): Path(Temp.TEMP).joinpath(name).with_suffix('.tmp').touch()

def off(name): remove(Path(Temp.TEMP).joinpath(name).with_suffix('.tmp'))

def is_on(name): return True if Path(Temp.TEMP).joinpath(name).with_suffix('.tmp').exists() else False
