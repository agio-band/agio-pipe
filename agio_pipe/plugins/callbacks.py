import logging
from agio.core.events import callback, AEvent
from agio.core.pkg import APackageManager
import importlib

logger = logging.getLogger(__name__)

@callback('core.app.all_packages_loaded')
def package_loaded(event: AEvent):
    logger.debug("Load entity classes")
    for pkg in event.payload['package_hub'].iter_packages():
        pkg: APackageManager
        entities_path = pkg.get_meta_data_field('project_entities_path', 'entities/*.py')
        files = list(pkg.root.glob(entities_path))
        for entity_module in files:
            if entity_module.name.startswith('_'):
                continue
            file_path_to_import_path = entity_module.relative_to(pkg.root).as_posix().rsplit('.', 1)[0].replace('/', '.')
            import_path = f"{pkg.package_name}.{file_path_to_import_path}"
            importlib.import_module(import_path)
