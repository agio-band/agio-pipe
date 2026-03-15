from agio.core.plugins.base_plugin import APlugin
from agio_pipe.publish.publish_session import PublishSession


class PublishEngineBasePlugin(APlugin):
    plugin_type = 'publish_engine'
    open_ui_function = None
    parameters = None

    def execute(self, session: PublishSession, **options) -> None:
        raise NotImplementedError()
