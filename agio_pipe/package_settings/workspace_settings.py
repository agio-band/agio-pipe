from typing import Optional

from agio.core.settings import APackageSettings, JSONField, PluginSelectField, ListField, StringField
from pydantic import BaseModel, Field

from agio.core.settings.fields.special_fields import ChipSelectField

# TemplateType = dict[str, str]


class PublishTemplate(BaseModel):
    name: str
    path: str = StringField(..., json_schema_extra=dict(widget='PathTemplate'))
    variables: dict[str, str] = Field(default_factory=dict)


class ReviewTemplates(BaseModel):
    name: str
    template: dict


class PipeWorkspaceSettings(APackageSettings):
    # plugins and chips
    publish_plugin: str = PluginSelectField('publish_engine')
    publish_scene_chip: str = ChipSelectField('publish_scene', default='default')
    # templates
    apply_burn_in: bool = True
    review_templates: Optional[list[ReviewTemplates]] = ListField(default=list)
    # publish processing
    publish_templates: Optional[list[PublishTemplate]] = ListField(default=list)
    align_product_versions: bool = False

