from __future__ import annotations

import logging
import traceback
from typing import Any

from agio.core.events import emit
from agio.core.utils import plugin_hub
from agio_pipe.entities import product as product_entity
from agio_pipe.entities import task as task_domain
from agio_pipe.entities.published_file import APublishedFile
from agio_pipe.entities.version import AVersion
from agio_pipe.publish.containers.export_container_base import ExportContainerBase
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.publish.publish_engine_base_plugin import PublishEngineBasePlugin
from agio_pipe.publish.publish_scene_base_plugin import PublishSceneBasePlugin
from agio_pipe.schemas.version import PublishedFileFull
from agio_publish_simple.ui.main_window import PublishDialog

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
            task_id: str| 'task_domain.ATask',
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
            id=container.id,
            name=container.name,
            task=task,
            product=product,
            sources=container.get_sources(),
            options=container.get_options(),
            # dependencies
            )
        return inst

    def open_dialog(self, **kwargs):
        ...

    def start_publishing(self, scene_file: str|dict = None,
                         return_result_only: bool = False, **options) -> list[PublishInstance] | list[dict]:
        publish_options = self.options.copy()
        publish_options.update(options)
        emit('pipe.publish.before_start', publish_options)
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
        if return_result_only:
            return result
        done_instances = []
        for item in result:
            instance: PublishInstance = item['instance']
            version = AVersion.create(
                product_id=instance.product.id,
                task_id=instance.task.id,
                version=instance.version,
            )
            files = []
            # try:
            for file in item['published_files']:
                file: PublishedFileFull
                published_file = APublishedFile.create(
                    version_id=version.id,
                    path=file.relative_path,
                )
                files.append({
                    **published_file.to_dict(),
                    'orig_path': file.orig_path # add original path
                })
            # except Exception as e:
            #     traceback.print_exc()
            #     version.delete()

            logger.info('Create version %s for %s %s/%s' % (
                instance.version,
                instance.task,
                instance.product.name, instance.product.variant,
            ))

            instance.set_results(version.to_dict(), files)
            done_instances.append(instance)
        return done_instances

    def get_engine_plugin(self) -> PublishEngineBasePlugin:
        plg_hub = plugin_hub.APluginHub.instance()
        # TODO: engine name order resolve: options, settings, default
        engine_name = self._options.get('engine_name', 'simple_publish')
        plugin = plg_hub.get_plugin_by_name('publish_engine', engine_name)
        if not plugin:
            raise ValueError(f"Plugin '{engine_name}' not found")
        return plugin

    def get_publish_scene_plugin(self, **options) -> PublishSceneBasePlugin:
        plg_hub = plugin_hub.APluginHub.instance()
        scene_plugin_name = options.get('scene_plugin_name')
        app_name = 'standalone' # TODO: get from current context
        if scene_plugin_name:
            scene_plugin = plg_hub.get_plugin_by_name('publish_scene', scene_plugin_name)
            if not scene_plugin:
                raise ValueError(f"Plugin '{scene_plugin_name}' not found")
            return scene_plugin
        elif app_name:
            for plugin in plg_hub.iter_plugins('publish_scene'):
                if plugin.app_name == app_name:
                    return plugin
            else:
                raise ValueError(f"Plugin 'publish_scene' for app '{app_name}' not found")
        else:
            raise ValueError(f"Can not resolve publish_scene plugin")
