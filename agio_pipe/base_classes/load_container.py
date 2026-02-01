from abc import abstractmethod

from agio.core.plugins import base_plugin


class LoadContainerBasePlugin(base_plugin.APlugin):
    __is_base_plugin__ = True
    plugin_type = 'load_container'

    def __init__(self, container, *args, **kwargs):
        super(LoadContainerBasePlugin, self).__init__(*args, **kwargs)

    @classmethod
    @abstractmethod
    def create(cls, product_version: AProductVersion):
        raise NotImplementedError()

    @abstractmethod
    def execute(self, **kwargs):
        raise NotImplementedError()

    @abstractmethod
    def validate(self):
        raise NotImplementedError()
