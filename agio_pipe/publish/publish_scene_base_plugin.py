from agio.core.plugins.base_plugin import APlugin
from agio.core.plugins.mixins import BasePluginClass
from agio_pipe.publish.instance import PublishInstance


class PublishSceneBasePlugin(BasePluginClass, APlugin):
    plugin_type = 'publish_scene'
    app_name = None

    def load_scene(self, scene_path: str = None, **options):
        raise NotImplementedError()

    def add_instance(self, instance: PublishInstance):
        raise NotImplementedError()

    def collect_instances_from_scene(self) -> list[PublishInstance]:
        raise NotImplementedError()

    def save_scene(self, scene_path: str = None, **options):
        raise NotImplementedError()