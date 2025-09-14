from collections import defaultdict
from pathlib import Path
import json


# noinspection PyInconsistentReturns
class Dictionary(dict):

    @property
    def _constructor(self):
        return self.__class__


    @staticmethod
    def _convert_to_this(json_dict: dict):
        return Dictionary(json_dict)


    def write(self, pathname: Path):
        print(f'writing dictionary as json to "{pathname}"')
        with open(pathname, 'w', encoding='utf-8') as f:
            json.dump(self, f)
        return pathname


    def __init__(self, *args, json_source: Path = None, **kwargs):
        super().__init__(*args, **kwargs)

        if json_source is not None and json_source.exists():
            self.clear()
            try:
                print(f'reading json file "{json_source}" into dictionary')
                with open(json_source, 'r', encoding='utf-8') as f:
                    data = json.load(f, object_hook=self._convert_to_this)
                if not isinstance(data, dict):
                    raise ValueError(f'JSON file must contain a dictionary, got {type(data).__name__}')
                self.update(data)
            except json.JSONDecodeError as e:
                print(e)


    def invert(self):
        # create new dictionary
        #      original values become the new keys
        #      original keys are in arrays as the new values (original values may not be unique)
        reverse_map = defaultdict(list)
        for key, value in self.items():
            reverse_map[value].append(key)
        return Dictionary(reverse_map)
