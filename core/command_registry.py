from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class CommandDef:
    code: str
    label: str
    color: str
    hidden: bool = False


class CommandRegistry:
    """
    Single responsibility:
    Provide command definitions (label/color/hidden) from loaded config.
    """

    def __init__(self, commands_dict: Dict[str, dict]):
        self._commands: Dict[str, CommandDef] = {}
        for code, meta in commands_dict.items():
            self._commands[code] = CommandDef(
                code=code,
                label=str(meta.get("label", code)),
                color=str(meta.get("color", "#505050")),
                hidden=bool(meta.get("hidden", False)),
            )

    def get(self, code: str) -> Optional[CommandDef]:
        return self._commands.get(code)

    def all(self, include_hidden: bool = False) -> List[CommandDef]:
        cmds = list(self._commands.values())
        return [c for c in cmds if include_hidden or not c.hidden]
