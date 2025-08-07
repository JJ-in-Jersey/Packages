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


    def __init__(self, *args, json_source: Path = None, dict_path: str = None, **kwargs):
        super().__init__(*args, **kwargs)

        self._path = dict_path

        if json_source is not None and json_source.exists():
            self.clear()
            try:
                print(f'reading json file "{json_source}" into dictionary')
                with open(json_source, 'r', encoding='utf-8') as f:
                    data = json.load(f, object_hook=self._convert_to_this)
                if not isinstance(data, dict):
                    raise ValueError(f'JSON file must contain a dictionary, got {type(data).__name__}')
                self.update(data)
                # After loading, set path and parent
                self._set_path()
            except json.JSONDecodeError as e:
                print(e)

    def _set_path(self, _path: str = ""):
        self['_path'] = _path
        for key, value in self.items():
            if isinstance(value, Dictionary):
                value._set_path(f"{_path}/{key}" if _path else key)


    def write(self, pathname: Path):
        print(f'writing dictionary as json to "{pathname}"')
        with open(pathname, 'w', encoding='utf-8') as f:
            json.dump(self, f)
        return pathname


    def invert(self):
        # create new dictionary
        #      original values become the new keys
        #      original keys are in arrays as the new values (original values may not be unique)
        reverse_map = defaultdict(list)
        for key, value in self.items():
            reverse_map[value].append(key)
        return Dictionary(reverse_map)


    def remove_keys(self, target_key, remove_all=True, _removed_keys=None):
        """
        remove key-value pairs based on the key

        Args:
            target_key: The key to search for and remove
            remove_all (bool): true removes all occurrences; false removes only the first occurrence.
            _removed_keys (list): Internal parameter for collecting removed items

        Returns:
            list: List of tuples (path, key) that were removed
        """
        if _removed_keys is None:
            _removed_keys = []

        keys_to_remove = []

        for key, value in self.items():
            if key == target_key:
                # Found a matching key at this level
                current_path = f"{self['_path']}/{key}" if self['_path'] else key
                keys_to_remove.append(key)
                _removed_keys.append((current_path, key))
                print(f"Removing: {current_path}")

                # If only removing the first occurrence, stop after finding one
                if not remove_all:
                    break
            elif isinstance(value, Dictionary):
                # Recursively search nested dictionaries
                value.remove_keys(target_key, remove_all, _removed_keys)
                # If we only want first occurrence, stop
                if not remove_all and len(_removed_keys) > 0:
                    break

        # Remove the found items from this level
        for key in keys_to_remove:
            del self[key]

        return _removed_keys


    def print_tree_structure(self, indent=0, max_depth=None):
        """
        Print the tree structure in a readable format
        :param indent: current indentation level
        :param max_depth: maximum depth to print (None for unlimited)
        """
        if max_depth is not None and indent >= max_depth:
            return

        for name, item in self.items():
            if isinstance(item, dict):
                icon = "📁" if item.get('type') == 'folder' else "📄"
                print("  " * indent + f"{icon} {name}")

                # Print children if it's a folder
                if item.get('type') == 'folder' and 'children' in item:
                    self.print_tree_structure(indent + 1, max_depth)


    def get_tree_stats(self):
        """
        Get statistics about the file tree
        :return: dictionary with stats
        """
        stats = {
            'total_files': 0,
            'total_folders': 0,
            'max_depth': 0,
            'mime_types': {}
        }

        def _analyze_recursive(node, depth=0):
            stats['max_depth'] = max(stats['max_depth'], depth)

            if isinstance(node, dict):
                if node.get('type') == 'file':
                    stats['total_files'] += 1
                    mime_type = node.get('mimeType', 'unknown')
                    stats['mime_types'][mime_type] = stats['mime_types'].get(mime_type, 0) + 1
                elif node.get('type') == 'folder':
                    stats['total_folders'] += 1
                    if 'children' in node:
                        for child in node['children'].values():
                            _analyze_recursive(child, depth + 1)

        for item in self.values():
            _analyze_recursive(item)

        return stats


    def find_keys(self, target_key, target_value=None, _found_keys=None):
        """
        retrieve key/value pairs that match the target_key
        :param target_key: key to be found
        :param get_all (bool): true returns all occurrences; false returns only the first occurrence
        :param _found_keys: list of found items, passed to next recursion
        :return _found_keys: list of found item tuples (key, value)
        """
        if _found_keys is None:
            _found_keys = []

        for key, value in self.items():
            if key == target_key:
                if target_value is not None:
                    if value == target_value:
                        _found_keys.append((f'{self['_path']}/{key}' if self['_path'] else {key}, value))
                else:
                    _found_keys.append((f'{self['_path']}/{key}' if self['_path'] else {key}, value))
            if isinstance(value, Dictionary):
                value.find_keys(target_key, target_value, _found_keys)
        return _found_keys


    def del_key(self, key_path: str):
        splits = key_path.split('/')
        del_dict = self
        for folder in splits[:-1]:
            del_dict = del_dict[folder]
        print(f'del {key_path}')
        del del_dict[splits[-1]]


    def parent(self, path: str):
        splits = path.split('/')
        p = self
        for folder in splits[:-1]:
            p = p[folder]
        return p
