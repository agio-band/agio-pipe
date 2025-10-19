import json

from agio_pipe.exceptions import InstanceDuplicateError
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.publish.publish_scene_base_plugin import PublishSceneBasePlugin


class PublishSceneStandalonePlugin(PublishSceneBasePlugin):
    name = "publish_scene_standalone"
    app_name = 'standalone'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = {'containers': []}

    def load_scene(self, scene_path: str = None, **options):
        with open(scene_path, 'r') as scene_file:
            self.scene = json.load(scene_file)

    def collect_instances_from_scene(self) -> list[PublishInstance]:
        instances = []
        if self.scene:
            for cont in self.scene.get('containers', []):
                instances.append(PublishInstance(**cont))
        return instances

    def add_instance(self, instance: PublishInstance):
        if instance not in self.collect_instances_from_scene():
            raise InstanceDuplicateError
        self.scene['containers'].append(instance.to_dict())
        return True

    def save_scene(self, scene_path: str = None, **options):
        with open(scene_path, 'w') as scene_file:
            json.dump(self.scene, scene_file, indent=2)
