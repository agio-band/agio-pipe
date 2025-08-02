from agio.core.domains import AProductVersion
from agio.core.plugins.base_plugin import APlugin
from agio.core.plugins.mixins import BasePluginClass
from agio_pipe.publish.instance import PublishInstance


class PublishEngineBasePlugin(BasePluginClass, APlugin):
    plugin_type = 'publish_engine'
    parameters = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instances: dict[str, PublishInstance] = {}

    def execute(self, **options) -> list[AProductVersion]:
        raise NotImplementedError()

    def add_instances(self, *instances: PublishInstance):
        for inst in instances:
            if inst.id in self.instances:
                raise ValueError(f"Instance {inst} already exists")
        self.instances.update({inst.id: inst for inst in instances})

    def remove_instance(self, instance_id: str):
        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not registered")



