import json
from pathlib import Path
from typing import Any, Dict


class ConfigStore:
    """
    Single responsibility:
    Read/write JSON config files from the /config directory.
    """

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.config_dir = base_dir / "config"

    def read_json(self, filename: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
        path = self.config_dir / filename
        if not path.exists():
            return default or {}
        return json.loads(path.read_text(encoding="utf-8"))

    def write_json(self, filename: str, data: Dict[str, Any]) -> None:
        path = self.config_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
