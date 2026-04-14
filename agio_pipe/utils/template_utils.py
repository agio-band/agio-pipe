import re
from fnmatch import fnmatch
from pathlib import Path


def filter_template(path: Path, template_options: list[dict], context: dict=None) -> dict:
    # TODO: add filter logic for context
    for template in template_options:
        if 'filter' in template:
            if fnmatch(path.name, template['filter']):
                return template
            else:
                continue
        elif 'regex_filter' in template:
            if re.match(template['regex_filter'], path.name, ):
                return template
            else:
                continue
        else:
            return template
    raise Exception(f'Template name not found for file {path.name}')