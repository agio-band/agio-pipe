from enum import StrEnum, auto
from typing import Optional

from agio.core.settings import APackageSettings, JSONField, PluginSelectField, ListField, StringField
from pydantic import BaseModel, Field

from agio.core.settings.fields.special_fields import ChipSelectField


class AlignVersions(StrEnum):
    NONE = auto()
    PRODUCTS = auto()
    ALL = auto()


class PublishTemplate(BaseModel):
    name: str
    path: str = StringField(..., json_schema_extra=dict(widget='PathTemplate'))
    variables: dict[str, str] = Field(default_factory=dict)


class ReviewTemplates(BaseModel):
    name: str
    template: dict


class WebProductSettings(BaseModel):
    product_name: str
    publish_template_name: str
    file_type_list: list[str] = ['*']
    required: bool = False


class WebPublisherSettings(BaseModel):
    products: list[WebProductSettings] = Field(default_factory=list)


class PipeWorkspaceSettings(APackageSettings):
    # plugins and chips
    publish_plugin: str = PluginSelectField('publish_engine')
    publish_scene_chip: str = ChipSelectField('publish_scene', default='default')
    # templates
    apply_burn_in: bool = True
    review_templates: Optional[list[ReviewTemplates]] = ListField(default=list)
    # publish processing
    publish_templates: Optional[list[PublishTemplate]] = ListField(default=list)
    publication_name_template: str = '{publication_entity.parent.name}_{publication_entity.name}_v{publication_version}'
    align_product_versions: AlignVersions = AlignVersions.NONE
    # web publisher settings
    web_publisher_settings: WebPublisherSettings = WebPublisherSettings()

