from enum import auto
from agio.tools.enum import StrEnum
from typing import Optional

from agio.core.settings import APackageSettings, PluginSelectField, ListField, StringField, DictField
from pydantic import BaseModel, Field

from agio.core.settings.fields.special_fields import ChipSelectField


class AlignVersions(StrEnum):
    NONE = auto()
    PRODUCTS = auto() # published products only
    ALL = auto() # published products and session


class TemplateString(BaseModel):
    name: str
    template: str = Field(..., json_schema_extra=dict(widget='Template'))
    variables: dict[str, str] = Field(default=dict)


class PublicationNameTemplate(TemplateString):
    pass


class PublishPathTemplate(TemplateString):
    pass


class ProductNameTemplate(TemplateString):
    pass


class ReviewTemplates(BaseModel):
    name: str
    template: dict = DictField(..., json_schema_extra=dict(widget='Template'))
    variables: dict[str, str] = Field(default_factory=dict)
    defaults: dict[str, str] = Field(default_factory=dict)


class WebProductSettings(BaseModel):
    product_name: str
    publish_template_name: str
    file_type_list: list[str] = ['*']
    required: bool = False


class WebPublisherSettings(BaseModel):
    products: list[WebProductSettings] = ListField(default=list)


def _default_publication_name():
    return [PublicationNameTemplate(
        name='default',
        template='{publication_entity.parent.name}_'
                 '{publication_entity.name}_'
                 'v{publication_version:0{version_padding}d}'
    )]


class PipeWorkspaceSettings(APackageSettings):
    # plugins and chips
    publish_plugin: str = PluginSelectField('publish_engine')
    publish_scene_chip: str = ChipSelectField('publish_scene', default='default')

    # publish processing
    publication_name_templates: list[PublicationNameTemplate] = ListField(default=_default_publication_name)
    product_name_templates: list[ProductNameTemplate] = ListField(default=list)
    publish_templates: Optional[list[PublishPathTemplate]] = ListField(default=list)
    align_product_versions: AlignVersions = AlignVersions.NONE
    default_variant: str = ''
    default_frame_padding: int = 4
    default_version_padding: int = 3
    variant_list: list[str] = ListField(default=list)
    # web publisher settings
    web_publisher_settings: WebPublisherSettings = WebPublisherSettings()

    # TODO: MOVE TO REVIEW PACKAGE
    # templates
    apply_burn_in: bool = True
    review_templates: Optional[list[ReviewTemplates]] = ListField(default=list)



