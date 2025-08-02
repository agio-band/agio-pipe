from typing import Any

from agio.core.domains import AProductType
from agio.core.domains.variant import AVariant
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.publish.publish_engine_base_plugin import PublishEngineBasePlugin
from agio_pipe.publish.publish_scene_base_plugin import PublishSceneBasePlugin
from agio_pipe.entities.task import ATask


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
            product_type_id: str| AProductType,
            variant_id: str| AVariant,
            name: str = None,
            **kwargs
        ) -> PublishInstance:
        inst = PublishInstance(task_id, product_type_id, variant_id, name=name, **kwargs)
        self.add_instances(inst)
        return inst

    def start_publishing(self, scene_file: str = None, **options):
        publish_options = self.options.copy()
        publish_options.update(options)
        if scene_file is not None:
            scene_plugin = self.get_publish_scene_plugin(**options)
            scene_plugin.load_scene(scene_file)
            instances = scene_plugin.collect_instances_from_scene()
            if instances:
                self.add_instances(*instances)
        self.engine_plugin.execute(**publish_options)

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
