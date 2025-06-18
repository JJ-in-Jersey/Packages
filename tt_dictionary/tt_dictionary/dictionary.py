from pathlib import Path
import json


class Dictionary(dict):
    def __init__(self, json_source: Path = None, *args, **kwargs):
        self.source = json_source
        super().__init__(*args, **kwargs)

        if self.source is not None and self.source.exists():
            self.read()

    def read(self):
        self.clear()
        self.append(self.source)

    def append(self, pathname: Path):
        if pathname is not None:
            if not pathname.exists():
                raise FileExistsError(pathname)
            try:
                with open(pathname, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError(f'JSON file must contain a dictionary, got {type(data).__name__}')
                self.update(data)
            except json.JSONDecodeError as e:
                print(e)

    def write(self, pathname: Path):
        with open(pathname, 'w', encoding='utf-8') as f:
            json.dump(self, f)
        return pathname