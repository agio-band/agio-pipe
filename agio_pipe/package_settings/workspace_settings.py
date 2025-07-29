from typing import Optional

from agio.core.settings import APackageSettings, JSONField, PluginSelectField
from pydantic import BaseModel, Field


class PublishTemplate(BaseModel):
    name: str
    pattern: str = Field(..., widget='PathTemplate')


class PipeWorkspaceSettings(APackageSettings):
    publish_plugin: str = PluginSelectField('publish_engine')
    constants: dict|None = None
    apply_burn_in: bool = True
    templates: Optional[list[PublishTemplate]] = []