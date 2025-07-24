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

    def __init__(self, *args, json_source: Path = None, **kwargs):
        super().__init__(*args, **kwargs)

        if json_source is not None and json_source.exists():
            self.clear()
            try:
                print(f'reading json file "{json_source}" into dictionary')
                with open(json_source, 'r', encoding='utf-8') as f:
                    data = json.load(f, object_hook=Dictionary._convert_to_this)
                if not isinstance(data, dict):
                    raise ValueError(f'JSON file must contain a dictionary, got {type(data).__name__}')
                self.update(data)
            except json.JSONDecodeError as e:
                print(e)



    def write(self, pathname: Path):
        print(f'writing dictionary as json to "{pathname}"')
        with open(pathname, 'w', encoding='utf-8') as f:
            json.dump(self, f)
        return pathname


    def reverse(self):
        # create new dictionary
        #      original values become the new keys
        #      original keys are in arrays as the new values (original values may not be unique)
        reverse_map = defaultdict(list)
        for key, value in self.items():
            reverse_map[value].append(key)
        return dict(reverse_map)


    def recursive_get_key(self, target_key: str, dict_path: list[str] = None):
        # find the first instance of a dict/value pair a Dictionary that may contain Dictionaries
        instances = []
        if dict_path is None:
            dict_path = []

        for key, value in self.items():
            item_dict_path = " > ".join(dict_path + [key])
            if key == target_key:
                instances.append(tuple([item_dict_path, key, value]))
            elif isinstance(value, Dictionary):
                instances.extend(value.recursive_get_key(target_key, dict_path + [key]))
        return instances


    def remove_key(self, key: str):
        occurances = self.recursive_get_key(key)
        for occurance in occurances:
            fields = [x.strip() for x in occurance[0].split('>')]
            curr_dict = self
            for field in fields[:-1]:
                if isinstance(curr_dict, Dictionary) and field in curr_dict:
                    curr_dict = curr_dict[field]
            print(f'removing {key} from {field}')
            if curr_dict.get(key):
                curr_dict.pop(key)
