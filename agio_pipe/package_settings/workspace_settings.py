from enum import auto
from agio.tools.enum import StrEnum
from typing import Optional

from agio.core.settings import APackageSettings, PluginSelectField, ListField, StringField, DictField
from pydantic import BaseModel

from agio.core.settings.fields.special_fields import ChipSelectField


class AlignVersions(StrEnum):
    NONE = auto()
    PRODUCTS = auto() # published products only
    ALL = auto() # published products and session


class PublishPathTemplate(BaseModel):
    name: str
    path: str = StringField(..., json_schema_extra=dict(widget='PathTemplate'))
    variables: dict[str, str] = DictField(default=dict)


class ProductNameTemplate(BaseModel):
    name: str
    pattern: str


class ReviewTemplates(BaseModel):
    name: str
    template: dict


class WebProductSettings(BaseModel):
    product_name: str
    publish_template_name: str
    file_type_list: list[str] = ['*']
    required: bool = False


class WebPublisherSettings(BaseModel):
    products: list[WebProductSettings] = ListField(default=list)


class PipeWorkspaceSettings(APackageSettings):
    # plugins and chips
    publish_plugin: str = PluginSelectField('publish_engine')
    publish_scene_chip: str = ChipSelectField('publish_scene', default='default')
    # publish processing
    publish_templates: Optional[list[PublishPathTemplate]] = ListField(default=list)
    publication_name_template: str = '{publication_entity.parent.name}_{publication_entity.name}_v{publication_version:03d}' # TODO make as list
    product_name_templates: list[ProductNameTemplate] = ListField(default=list)
    align_product_versions: AlignVersions = AlignVersions.NONE
    default_variant: str = ''
    variant_list: list[str] = ListField(default=list)
    # web publisher settings
    web_publisher_settings: WebPublisherSettings = WebPublisherSettings()

    # TODO: MOVE TO REVIEW PACKAGE
    # templates
    apply_burn_in: bool = True
    review_templates: Optional[list[ReviewTemplates]] = ListField(default=list)

