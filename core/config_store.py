import json
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigStore:
    """
    Single responsibility:
    Read/write JSON config files from the /config directory.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.config_dir = base_dir / "config"

    def read_json(
        self,
        filename: str,
        default: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        path = self.config_dir / filename

        if not path.exists():
            return default or {}

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_json(self, filename: str, data: Dict[str, Any]) -> None:
        path = self.config_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
