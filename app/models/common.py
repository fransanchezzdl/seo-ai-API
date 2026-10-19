"""Tipos compartidos y utilidades de validación."""

import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def words(text: str) -> list[str]:
    return re.findall(r"\b\w+(?:[-’']\w+)*\b", text, flags=re.UNICODE)


def unique(values: list[str]) -> bool:
    return len({v.casefold() for v in values}) == len(values)
