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
        return Dictionary(reverse_map)


    def recursive_get_key(self, target_key, dict_path=None):
        if dict_path is None:
            dict_path = []

        if target_key in self:
            return dict_path + [target_key], self[target_key]

        for key, value in self.items():
            if isinstance(value, Dictionary):
                result = value.recursive_get_key(target_key, dict_path + [key])
                if result is not None:
                    return result

        return None


    def recursive_get_keys(self, target_key, dict_path=None):
        if dict_path is None:
            dict_path = []

        results = []

        if target_key in self:
            results.append((dict_path + [target_key], self[target_key]))

        for key, value in self.items():
            if isinstance(value, Dictionary):
                nested_results = value.recursive_get_keys(target_key, dict_path + [key])
                results.extend(nested_results)

        return results

    def get_by_path(self, path):
        current = self
        for key in path:
            current = current[key]
        return current

    def set_by_path(self, path, value):
        current = self
        for key in path[:-1]:
            if key not in current:
                raise KeyError(f"Key '{key}' not found in path {path}")
            elif not isinstance(current[key], Dictionary):
                raise ValueError(f"Cannot traverse through non-dict value at key '{key}'")
            current = current[key]

        current[path[-1]] = value

    def remove_by_path(self, path):
        current = self
        for key in path[:-1]:
            if key not in current:
                raise KeyError(f"Key '{key}' not found in path {path}")
            elif not isinstance(current[key], Dictionary):
                raise ValueError(f"Cannot traverse through non-dict value at key '{key}'")
            current = current[key]

        if path[-1] not in current:
            raise KeyError(f"Key '{path[-1]}' not found in path {path}")

        return current.pop(path[-1])


    def get_by_value(self, target_value, get_all=False, current_path=None):

        if current_path is None:
            current_path = []

        found_items = []

        for key, value in self.items():
            if isinstance(value, Dictionary):
                nested_found = value.get_by_value(target_value, get_all, current_path + [key])

                if get_all:
                    found_items.extend(nested_found)
                else:
                    if nested_found is not None:
                        return nested_found
            else:
                if value == target_value:
                    result = (current_path + [key], value)
                    if get_all:
                        found_items.append(result)
                    else:
                        return result

        return found_items if get_all else None


    def remove_by_value(self, target_value, remove_all=False, _path="", _removed_items=None):
        """
        Remove key-value pairs based on the value.

        Args:
            target_value: The value to search for and remove
            all_occurrences (bool): If True, removes all occurrences.
                                   If False, removes only the first occurrence.
            _path (str): Internal parameter for tracking current path
            _removed_items (list): Internal parameter for collecting removed items

        Returns:
            list: List of tuples (key, value) that were removed
        """
        if _removed_items is None:
            _removed_items = []

        keys_to_remove = []

        for key, value in self.items():
            current_path = f"{_path}/{key}" if _path else key

            if isinstance(value, dict):
                # Recursively search nested dictionaries
                # The nested dict will handle its own deletions
                value.remove_by_value(target_value, remove_all, current_path, _removed_items)
            elif value == target_value:
                # Found a matching value at this level
                keys_to_remove.append(key)
                _removed_items.append((current_path, value))
                print(f"Removing: {current_path} = {value}")

                # If only removing first occurrence, stop after finding one
                if not remove_all and _removed_items:
                    break

        # Remove the found items from this level
        for key in keys_to_remove:
            del self[key]

        return _removed_items


    def remove_by_key(self, target_key, remove_all=False, _path="", _removed_items=None):
        """
        Remove key-value pairs based on the key.

        Args:
            target_key: The key to search for and remove
            remove_all (bool): If True, removes all occurrences.
                              If False, removes only the first occurrence.
            _path (str): Internal parameter for tracking current path
            _removed_items (list): Internal parameter for collecting removed items

        Returns:
            list: List of tuples (key, value) that were removed
        """
        if _removed_items is None:
            _removed_items = []

        keys_to_remove = []

        for key, value in self.items():
            current_path = f"{_path}/{key}" if _path else key

            if key == target_key:
                # Found a matching key at this level
                keys_to_remove.append(key)
                _removed_items.append((current_path, value))
                print(f"Removing: {current_path} = {value}")

                # If only removing first occurrence, stop after finding one
                if not remove_all and _removed_items:
                    break
            elif isinstance(value, dict):
                # Recursively search nested dictionaries
                # The nested dict will handle its own deletions
                value.remove_by_key(target_key, remove_all, current_path, _removed_items)

        # Remove the found items from this level
        for key in keys_to_remove:
            del self[key]

        return _removed_items