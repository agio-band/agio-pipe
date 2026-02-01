import os
from pathlib import Path

import yaml

from agio.core.entities.entity import AEntity
from agio_pipe.entities.product import AProduct
from agio_pipe.entities.product_type import AProductType
from agio_pipe.entities.task import ATask
from agio_pipe.publish.instance import PublishInstance
from .template_solver import TemplateSolver


def create_product_from_template(
        product_template: dict,
        entity: str|AEntity,
        task: str|ATask = None,
        variant: str = 'main',
        context: dict=None,
        extra_fields: dict = None,
        store_templates: bool = True,
    ) -> AProduct:
    """
    Template Example:
        product_type_id: UUID
        task_types: [ANIM, COMP]
        product_name_template: 'prodict_default'
        publish_file_template: 'publish_file_name'
        publish_dir_template: 'publish_dir'
        fields: {}
    """
    if isinstance(entity, str):
        entity = AEntity.from_id(entity)
    if not variant or not isinstance(variant, str):
        raise ValueError('Variant must be specified as non empty string')
    if not AProduct.validate_variant_name(variant):
        raise ValueError(f'Invalid variant name {variant}')
    if 'product_name_template' not in product_template:
        raise ValueError('product_name_template must be specified')
    if 'publish_dir_template' not in product_template:
        raise ValueError('publish_dir_template must be specified')
    context = context or {}
    # solve product name
    templates = _load_templates(entity.project)
    for t_name in (
            product_template['product_name_template'],
            product_template['publish_file_template'],
            product_template['publish_dir_template'],
        ):
        if t_name not in templates:
            raise ValueError(f'template name {t_name} not found in project settings')
    product_type = AProductType(product_template['product_type_id'])
    render_context = {
        'entity': entity,
        'project': entity.project,
        'product_type': product_type,
        **(context or {})
    }

    if task:
        render_context['task'] = task
    solver = TemplateSolver(templates)

    # product name
    product_name_template_name = product_template['product_name_template']
    product_name_template = templates[product_name_template_name]
    variables = solver.get_variables(product_name_template_name)
    # missing = set(variables) - set(context.keys())
    # if missing:
    #     raise ValueError(f'Missing variables in context which used in template: {missing}')

    # using variant in product name is disabled
    if 'variant' in variables:
        raise ValueError(
            f'Do not use variant variable in product name template : {templates[product_name_template_name]}')
    product_name = solver.solve(product_name_template_name, render_context)
    if not product_name.strip():
        raise ValueError('product_name resolved as empty string from template ')
    # check is unique name and variant
    if AProduct.find(entity_id=entity.id, name=product_name, variant=variant):
        raise NameError(f"Product {product_name} with variant {variant} already exists for entity {entity}")

    # publish file name
    publish_file_template_name = product_template['publish_file_template']

    # publish dir
    publish_dir_template_name = product_template['publish_dir_template']
    variables = solver.get_variables(publish_dir_template_name)
    if not 'version' in variables:
        raise ValueError('version variable is required for publish path template')

    # collect fields
    extra_fields = extra_fields or {}
    fields = extra_fields.copy()
    fields.update({
        **product_template.get('fields', {}),
        'publish_file_template_name': product_template['publish_file_template'],
        'publish_dir_template_name': product_template['publish_dir_template'],
        'hidden': product_template.get('hidden', False),
    })
    if store_templates:
        publish_file = solver.solve_partial(publish_file_template_name, render_context)
        publish_path = solver.solve_partial(publish_dir_template_name, render_context)
        fields.update({
            'product_name_template': product_name_template,
            'publish_file_template': publish_file,
            'publish_dir_template': publish_path,
        })
    # create product
    product = AProduct.create(
        entity_id=entity.id,
        name=product_name,
        product_type_id=product_type.id,
        variant=variant,
        fields=fields,
    )
    return product


def _load_templates(project):
    project_settings = project.get_settings()
    templates = project_settings.get('agio_pipe.publish_templates', [])
    return {template.name: template.pattern for template in templates}


def get_product_templates(project)->dict|None:
    # TODO: load from settings
    templates_path = os.getenv('AGIO_PRODUCT_TEMPLATES_PATH')
    if not templates_path:
        raise ValueError('AGIO_PRODUCT_TEMPLATES_PATH environment variable is not set')
    templates_file = Path(templates_path, project.code).with_suffix('.yml')
    if not templates_file.exists():
        return {}
    with templates_file.open() as f:
        return yaml.safe_load(f)


def create_product_instance(product: AProduct) -> PublishInstance:
    ...

