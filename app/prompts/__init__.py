from dataclasses import dataclass
from pathlib import Path

import yaml
from fastapi import HTTPException, status

_PROMPTS_DIR = Path(__file__).parent


@dataclass(frozen=True)
class PromptTemplate:
    system: str
    user: str

    def render(self, **vars: object) -> tuple[str, str]:
        return self.system.format(**vars), self.user.format(**vars)


def load(name: str) -> PromptTemplate:
    path = _PROMPTS_DIR / f"{name}.yaml"
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unknown prompt_template: {name}",
        )

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    system = data.get("system")
    user = data.get("user")
    if not isinstance(system, str) or not isinstance(user, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid prompt template (need 'system' and 'user' strings): {name}",
        )
    return PromptTemplate(system=system, user=user)
