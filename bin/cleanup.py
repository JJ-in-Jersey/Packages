import os
import shutil

dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
walk = os.walk(dir_path)
for x in walk:
    if 'venv' not in x[0] and os.path.basename(x[0]) == 'build':
        print(f'Deleting {x[0]}')
        shutil.rmtree(x[0])
    if 'venv' not in x[0] and 'egg-info' in os.path.basename(x[0]):
        print(f'Deleting {x[0]}')
        shutil.rmtree(x[0])

pass
