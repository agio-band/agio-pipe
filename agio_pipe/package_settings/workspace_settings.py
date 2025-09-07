from typing import Optional

from agio.core.settings import APackageSettings, JSONField, PluginSelectField
from pydantic import BaseModel, Field


class PublishTemplate(BaseModel):
    name: str
    root_name: str = None
    pattern: str = Field(..., widget='PathTemplate')


class PipeWorkspaceSettings(APackageSettings):
    publish_plugin: str = PluginSelectField('publish_engine')
    publish_templates: Optional[list[PublishTemplate]] = []

    apply_burn_in: bool = True
    review_template: str = JSONField(...)
