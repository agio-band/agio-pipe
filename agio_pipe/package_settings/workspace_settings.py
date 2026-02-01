from typing import Optional

from agio.core.settings import APackageSettings, JSONField, PluginSelectField
from pydantic import BaseModel, Field

from agio.core.settings.fields.special_fields import ChipSelectField


class PublishTemplate(BaseModel):
    name: str
    # root_name: str = None
    pattern: str = Field(..., widget='PathTemplate')


class PipeWorkspaceSettings(APackageSettings):
    # plugins and chips
    publish_plugin: str = PluginSelectField('publish_engine')
    publish_scene_chip: str = ChipSelectField('publish_scene', default='default')
    # templates
    publish_templates: Optional[list[PublishTemplate]] = []
    apply_burn_in: bool = True
    review_template: str = JSONField(...)
    # publish processing
    align_product_versions: bool = False

