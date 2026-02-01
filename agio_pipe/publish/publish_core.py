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
from agio_pipe.base_classes.protocols import PublishScene
from agio_pipe.entities.published_file import APublishedFile
from agio_pipe.entities.version import AVersion
from agio_pipe.exceptions import PublishError
from agio_pipe.publish.instance import PublishInstance
from agio_pipe.publish.publish_engine_base_plugin import PublishEngineBasePlugin
from agio_pipe.publish.publish_session import PublishSession
from agio_pipe.schemas.version import PublishedFileFull

logger = logging.getLogger(__name__)


class PublishCore:
    """
    Prepare instances and execute publish engine
    """
    def __init__(self, options: dict[str, Any] = None):
        self._options = options or {}
        self.engine_plugin: PublishEngineBasePlugin = self.get_engine_plugin()
        self.ws_settings: settings_hub.WorkspaceSettingsHub = AWorkspace.current().get_settings()

    def set_option(self, key: str, value: Any):
        self._options[key] = value

    def get_plugin_parameters(self) -> dict:
        return {}

    @property
    def options(self):
        return self._options

    def start_publishing(self, scene_file: str | dict = None,
                         return_result_only: bool = False,
                         **options) -> None:
        publish_options = copy.deepcopy(self.options)
        publish_options.update(options)
        emit('pipe.publish.before_start', {'publish_options': publish_options})
        # create or restore session
        session = PublishSession(session_id=options.pop('session_id', None))
        # open scene of provided
        if scene_file is not None:
            # get publish scene class for current app
            scene_cls = self.get_scene_api_class(publish_options)
            # load file
            scene_plugin = scene_cls()
            scene_plugin.load(scene_file)
            # collect instances
            for cont in scene_plugin.iter_scene_containers():
                cont: ExportContainerBase
                inst = self._create_instance_from_container(cont)
                logger.info('Instance created: %s', inst)
                session.add_instance(inst)
        # get publish plugin
        publish_plugin = self.get_engine_plugin()
        # start processing
        with session:
            publish_plugin.execute(session, **self.get_plugin_parameters(), **publish_options)

    def _create_instance_from_container(self, container: ExportContainerBase) -> PublishInstance:
        return PublishInstance(
            # id=container.id,
            task=container.get_task(),
            product=container.get_product(),
            sources=container.get_sources(),
            name=container.name,
            options=container.get_options(),
            # dependencies
            # metadata
            # data
        )

    def _start_publishing_(self, scene_file: str|dict = None,
                         return_result_only: bool = False, **options) -> list[PublishInstance] | list[dict]:
        """
        scene_file: file to open before start publishing
        """
        publish_options = copy.deepcopy(self.options)
        publish_options.update(options)
        emit('pipe.publish.before_start', {'publish_options': publish_options})
        if scene_file is not None:
            # get publish scene class for current app
            scene_cls = self.get_scene_api_class(publish_options)
            # load file
            scene_plugin: PublishScene = scene_cls()
            scene_plugin.load(scene_file)
            # collect containers and convert it to the instances
            for cont in scene_plugin.iter_scene_containers():
                inst = self.create_instance_from_container(cont)
                logger.info('Instance created: %s', inst)
                self.add_instances(inst)
        instances = self.get_instances()
        if not instances:
            raise PublishError('No instances to process')
        project_ids = set([inst.task.project_id for inst in instances])
        if len(project_ids) != 1:
            raise PublishError(detail=f'Multiple projects in single publish session is not supported ({len(project_ids)})')
        project = instances[0].project
        project_settings = project.get_settings()
        # sync versions
        if project_settings.get('agio_pipe.sync_instance_version_numbers', default=True): # TODO get from to different package. change parameter name
            max_version = max([inst.version for inst in self.get_instances()])
            logger.info('Max version: %s', max_version)
            for inst in self.get_instances():
                inst.set_version(max_version)
        emit('pipe.publish.before_publish_engine_execute', {'publish_options': publish_options, 'engine': self.engine_plugin})
        #### start publish ###
        logger.debug('Start publishing with engine "%s"', self.engine_plugin)
        result: list[dict] = self.engine_plugin.execute(**publish_options)
        ######################
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
            for file in item['published_files']:
                file: PublishedFileFull
                published_file = APublishedFile.create(
                    version_id=version.id,
                    path=file.relative_path,
                )
                published_file_data = {
                    **published_file.to_dict(),
                    'orig_path': file.orig_path # add original path
                }
                files.append(published_file_data)
            logger.info('Create version %s for %s %s/%s' % (
                instance.version,
                instance.task,
                instance.product.name, instance.product.variant,
            ))
            emit('pipe.publish.version_created', {'version': version})
            instance.set_results(version.to_dict(), files)
            done_instances.append(instance)

        emit('pipe.publish.after_publish_engine_execute', {'instances': done_instances, 'engine': self.engine_plugin})
        return done_instances

    def get_engine_name(self, options: dict[str, Any]) -> str:
        # from options
        if 'publish_engine_name' in options:
            return options['publish_engine_name']
        # from env
        publish_engine_name = os.getenv('AGIO_PUBLISH_ENGINE_NAME')
        if publish_engine_name:
            return publish_engine_name
        # from settings
        publish_engine_name = self.ws_settings.get('agio_pipe.publish_engine_name', default=None)
        if publish_engine_name:
            return publish_engine_name
        raise SettingsParameterNotExists('Parameter "publish_engine_name" is not defined')

    def get_engine_plugin(self) -> PublishEngineBasePlugin:
        engine_name = self.get_engine_name(self._options)
        plg_hub = plugin_hub.APluginHub.instance()
        plugin = plg_hub.get_plugin_by_name('publish_engine', engine_name)
        if not plugin:
            raise ValueError(f"Plugin '{engine_name}' not found")
        return plugin

    def get_scene_api_class(self,options: dict[str, Any]) -> Callable:
        chip_name = (options.get('publish_scene_chip_name') or
                    self.ws_settings.get('agio_pipe.publish_scene', default=None)
                     or 'default')
        cls = chips_hub.find_chip('publish_scene', chip_name)
        if not cls:
            raise ValueError(f"Chip 'scene_api.{chip_name}' not found")
        return cls
