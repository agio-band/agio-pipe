from agio.core.plugins.base_plugin import APlugin
from agio_pipe.publish.publish_session import PublishSession


class PublishEngineBasePlugin(APlugin):
    plugin_type = 'publish_engine'
    open_ui_function = None
    parameters = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session: PublishSession|None = None

    def execute(self, session: PublishSession, **options) -> None:
        self.session = session
        return self.start_publish(**options)

    def start_publish(self, **options):
        raise NotImplementedError()
