from typing import Dict


class KeyMap:
    """
    Single responsibility:
    Manage key bindings (validation + lookups) using a dict provided externally.
    Persistence is handled by whoever calls to_dict()/load_dict().
    """

    def __init__(self, mapping: Dict[str, str]):
        self._map: Dict[str, str] = {k: v.upper() for k, v in mapping.items()}

    def get_key(self, command: str) -> str:
        return self._map.get(command, "?")

    def get_all(self) -> Dict[str, str]:
        return dict(self._map)

    def update_key(self, command: str, new_key: str) -> None:
        new_key = new_key.upper().strip()
        if not new_key or len(new_key) != 1 or not new_key.isalnum():
            raise ValueError("Key must be a single alphanumeric character.")
        if new_key in self._map.values() and self._map.get(command) != new_key:
            raise ValueError(f"Key '{new_key}' is already assigned.")
        self._map[command] = new_key

    def get_command_from_key(self, key_char: str):
        key_char = key_char.upper()
        reverse_map = {v: k for k, v in self._map.items()}
        return reverse_map.get(key_char)
