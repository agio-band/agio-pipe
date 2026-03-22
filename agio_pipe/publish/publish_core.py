from __future__ import annotations

import copy
import logging
import os
from typing import Any, Callable

from agio.core.chips import chips_hub
from agio.core.entities import AWorkspace
from agio.core.events import emit
from agio.core.exceptions import SettingsParameterNotExists
from agio.core.plugins import plugin_hub
from agio.core.settings import settings_hub
from agio_pipe.base_classes.export_container import ExportContainerBase
from agio_pipe.exceptions import PublishError
from agio_pipe.publish import instance
from agio_pipe.publish.publish_engine_base_plugin import PublishEngineBasePlugin
from agio_pipe.publish import publish_session

logger = logging.getLogger(__name__)


class PublishCore:
    """
    Prepare instances and execute publish engine
    """
    def __init__(self, options: dict[str, Any] = None):
        self._options = options or {}
        self.ws = AWorkspace.current()
        self.settings: settings_hub.WorkspaceSettingsHub = self.ws.get_settings()

    def set_option(self, key: str, value: Any):
        self._options[key] = value

    def get_plugin_parameters(self) -> dict:
        return {}

    @property
    def options(self):
        return self._options

    def start_publishing(self, scene_file: str | dict = None, **options) -> publish_session.PublishSession:
        publish_options = copy.deepcopy(self.options)
        publish_options.update(options)
        emit('pipe.publish.before_start', {'publish_options': publish_options})
        # create or restore session
        session = publish_session.PublishSession(session_id=options.pop('session_id', None))
        # get publish scene class for current app
        scene_cls = self.get_scene_api_class(publish_options)
        scene_plugin = scene_cls()
        if scene_file is not None:
            # open scene of provided
            scene_plugin.load(scene_file)
        for cont in scene_plugin.iter_containers():
            cont: ExportContainerBase
            inst = instance.PublishInstance.from_export_container(cont)
            logger.info('Instance created: %s', inst)
            session.add_instance(inst)
        if not session.instances:
            raise PublishError('No instances to process')
        publish_plugin = self.get_engine_plugin()
        emit('pipe.publish.publish_plugin_created', {
            'publish_options': publish_options,
            'engine': publish_plugin,
            'session': session,
        })
        logger.info('Start publishing with engine "%s"', publish_plugin.__class__.__name__)
        # start main processing
        parameters = self.get_plugin_parameters()
        parameters.update(publish_options)
        parameters.update(options)
        logger.info('Session dump path %s', session.dump_file)
        with session:
            publish_plugin.execute(session, **parameters)
        return session

    def get_engine_name(self, options: dict[str, Any]) -> str:
        # from options
        if 'publish_engine_name' in options:
            return options['publish_engine_name']
        # from env
        publish_engine_name = os.getenv('AGIO_PUBLISH_ENGINE_NAME')
        if publish_engine_name:
            return publish_engine_name
        # from settings
        publish_engine_name = self.settings.get('agio_pipe.publish_plugin', default=None)
        if publish_engine_name:
            return publish_engine_name
        raise SettingsParameterNotExists('Parameter "agio_pipe.publish_plugin" is not defined')

    def get_engine_plugin(self) -> PublishEngineBasePlugin:
        engine_name = self.get_engine_name(self._options)
        plg_hub = plugin_hub.APluginHub.instance()
        plugin = plg_hub.get_plugin_by_name('publish_engine', engine_name)
        if not plugin:
            raise ValueError(f"Plugin '{engine_name}' not found")
        return plugin

    def get_scene_api_class(self,options: dict[str, Any]) -> Callable:
        chip_name = (options.get('publish_scene_chip_name') or
                    self.settings.get('agio_pipe.publish_scene', default=None)
                     or 'default')
        cls = chips_hub.find_chip('publish_scene', chip_name)
        if not cls:
            raise ValueError(f"Chip 'scene_api.{chip_name}' not found")
        return cls
