from typing import Optional
from pydantic import BaseModel

from agio.core.settings.package_settings import APackageSettings


class LocalRootsSettings(BaseModel):
    name: str
    path: str


class PipeLocalSettings(APackageSettings):
    local_roots: list[LocalRootsSettings] = []
