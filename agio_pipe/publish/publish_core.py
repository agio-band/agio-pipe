from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TYPE_CHECKING

from agio.core.events import emit
from agio.core.utils import file_tools
from agio_pipe.entities.version import AVersion
from agio_pipe.publish.containers.export_container_base import ExportContainerBase
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.publish.publish_engine_base_plugin import PublishEngineBasePlugin
from agio_pipe.publish.publish_scene_base_plugin import PublishSceneBasePlugin
from agio_pipe.entities import product as product_entity
from agio_pipe.entities.task import ATask
from agio_pipe.publish.published_file import PublishedFile

logger = logging.getLogger(__name__)


class PublishCore:
    """
    Prepare instances and execute publish engine
    """
    def __init__(self, options: dict[str, Any] = None):
        self._options = options or {}
        self.engine_plugin: PublishEngineBasePlugin = self.get_engine_plugin()

    def set_option(self, key: str, value: Any):
        self._options[key] = value

    def get_plugin_parameters(self):
        """
        TODO Parameter list of specific plugin
        """

    @property
    def options(self):
        return self._options

    def add_instances(self, *instances: PublishInstance):
        self.engine_plugin.add_instances(*instances)

    def remove_instance(self, instance: PublishInstance|str):
        self.engine_plugin.remove_instance(instance.id)

    def get_instances(self) -> list[PublishInstance]:
        return list(self.engine_plugin.instances.values())

    def create_instance(self,
            task_id: str| ATask,
            product_id: str| product_entity.AProduct,
            name: str = None,
            **kwargs
        ) -> PublishInstance:
        inst = PublishInstance(task_id, product_id, name=name, **kwargs)
        self.add_instances(inst)
        return inst

    def create_instance_from_container(self, container: ExportContainerBase) -> PublishInstance:
        task = container.get_task()
        product = container.get_product()
        inst = PublishInstance(
            name=container.name,
            task=task,
            product=product,
            sources=container.get_sources(),
            options=container.get_options(),
            # dependencies
            )
        return inst

    def start_publishing(self, scene_file: str = None, **options) -> list[AVersion]:
        emit('pipe.publish.add_report', {'publish_plugin': self.engine_plugin.name})  # TODO  user plugin name
        publish_options = self.options.copy()
        publish_options.update(options)
        if scene_file is not None:

            # TODO get current app scene plugin ##############
            # scene_plugin = self.get_publish_scene_plugin(**options)
            from agio_publish_simple.simple_scene.scene import SimplePublishScene
            # TODO ###########################################

            scene_plugin = SimplePublishScene(scene_file)
            containers = scene_plugin.get_containers()
            for cont in containers:
                inst = self.create_instance_from_container(cont)
                logger.info('Instance created: %s', inst)
                self.add_instances(inst)
        result: list[dict] = self.engine_plugin.execute(**publish_options)
        if not result:
            raise RuntimeError('Failed to execute publish engine. No result files')
        versions = []
        for item in result:
            instance: PublishInstance = item['instance']
            files = []
            for file in item['published_files']:
                file: PublishedFile
                file.size = Path(file.path).stat().st_size
                file.hash = file_tools.get_file_hash(file.path)
                files.append(file.model_dump(exclude=('path',)))
            fields = {'published_files': files}
            logger.info('Create version %s for %s %s/%s' % (
                instance.version,
                instance.task,
                instance.product.name, instance.product.variant,
                ))
            versions.append(AVersion.create(
                product_id=instance.product.id,
                task_id=instance.task.id,
                version_number=instance.version,
                fields=fields,
            ))
        return versions

    def get_engine_plugin(self) -> PublishEngineBasePlugin:
        from agio.core import plugin_hub

        # TODO: engine name order resolve: options, settings, default
        engine_name = self._options.get('engine_name', 'simple_publish')
        plugin = plugin_hub.get_plugin_by_name('publish_engine', engine_name)
        if not plugin:
            raise ValueError(f"Plugin '{engine_name}' not found")
        return plugin

    def get_publish_scene_plugin(self, **options) -> PublishSceneBasePlugin:
        from agio.core import plugin_hub
        scene_plugin_name = options.get('scene_plugin_name')
        app_name = 'standalone' # TODO: get from current context
        if scene_plugin_name:
            scene_plugin = plugin_hub.get_plugin_by_name('publish_scene', scene_plugin_name)
            if not scene_plugin:
                raise ValueError(f"Plugin '{scene_plugin_name}' not found")
            return scene_plugin
        elif app_name:
            for plugin in plugin_hub.iter_plugins('publish_scene'):
                if plugin.app_name == app_name:
                    return plugin
            else:
                raise ValueError(f"Plugin 'publish_scene' for app '{app_name}' not found")
        else:
            raise ValueError(f"Can not resolve publish_scene plugin")
