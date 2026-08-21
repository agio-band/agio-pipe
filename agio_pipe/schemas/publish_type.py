from pydantic import BaseModel


class TemplateFilter(BaseModel):
    name: str
    filter: str = '*'
    variables: dict = None # custom template variables


class ProductPublishOptions(BaseModel):
    publish_path_templates: list[TemplateFilter]
    supported_file_types: list[str]


class ProductConfigSchema(BaseModel):
    is_agio_type: bool = True
    options: ProductPublishOptions