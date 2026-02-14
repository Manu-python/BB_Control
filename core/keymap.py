class KeyMap:
    """
    Manages keyboard mappings for control commands.
    Handles validation, updates, and reverse lookups.
    """

    DEFAULT_MAP = {
        "A1": "W",
        "A2": "X",
        "A0": "S",
        "A3": "D",
        "A4": "A",
        "A5": "Q",
        "A6": "E",
        "A7": "Z",
        "A8": "C",
        "A9": "F",
        "A10": "R",
        "A11": "G",
        "A12": "T",
        "A13": "Y",
    }

    def __init__(self):
        self.map = self.DEFAULT_MAP.copy()

    # --- Getters ---

    def get_key(self, command: str) -> str:
        return self.map.get(command, "?")

    def get_all(self) -> dict:
        return self.map.copy()

    # --- Updates ---

    def update_key(self, command: str, new_key: str):
        new_key = new_key.upper().strip()

        if not new_key or len(new_key) != 1 or not new_key.isalnum():
            raise ValueError("Key must be a single alphanumeric character.")

        if new_key in self.map.values() and self.map.get(command) != new_key:
            raise ValueError(f"Key '{new_key}' is already assigned.")

        self.map[command] = new_key

    # --- Reverse Lookup ---

    def get_command_from_key(self, key_char: str):
        key_char = key_char.upper()
        reverse_map = {v: k for k, v in self.map.items()}
        return reverse_map.get(key_char)
