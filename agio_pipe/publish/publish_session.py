from __future__ import annotations

import json
import logging
import tempfile
import traceback
from collections import defaultdict
from enum import StrEnum
from functools import cached_property
from pathlib import Path
from typing import Any, Generator, Union
from uuid import UUID

from agio.core.entities import AWorkspace, AEntity
from agio.core.entities.publish_session import APublishSession
from agio.core.entities.task import ATask
from agio.core.entities.version import AVersion
from agio.core.events import emit
from agio.core.settings.settings_hub import WorkspaceSettingsHub
from agio.tools.data_helpers import deep_tree
from agio.tools.json_serializer import to_simple_dict
from agio_pipe.utils import template_solver
from . import instance as inst
from .instance import PublishInstance
from .session_store import SessionStore
from .tools.create_version import create_product_version
from ..exceptions import PublishError

logger = logging.getLogger(__name__)


class PublishSession:

    class STATUS(StrEnum):
        PENDING = 'PENDING'
        IN_PROGRESS = 'IN_PROGRESS'
        DONE = 'DONE'
        FAILED = 'FAILED'
        CANCELED = 'CANCELED'
        SYNC = 'SYNC'

    def __init__(self, session_id: str = None, task_id: str|UUID = None,
                 workspace_id: str = None, store_helper_class = None,
                 delete_on_error: bool = False,
                 **kwargs) -> None:
        self._kwargs = kwargs
        self.delete_on_error = delete_on_error
        self.id: str = session_id
        self._store_class = store_helper_class or SessionStore
        self.store_helper = None
        self._data: dict = self._init_session_data(session_id)
        if self._data:
            if task_id and task_id != self._data.get('task_id'):
                raise ValueError(f'Session {session_id} already used with task_id: {self._data.get("task_id")}')
            self._task_id = self._data.get('task_id')
        else:
            if not task_id:
                raise ValueError('Task ID is required for publish session')
            self._task_id = task_id
        self.settings = self._init_settings(workspace_id)
        self._dry_run = False
        self._session: APublishSession|None = None
        self._versions = []
        self.__is_context_manager_opened = False

    def _set_id(self, session_id):
        """Set id and recreate helper"""
        self.id = session_id
        self.store_helper = self._store_class(session_id)

    def __enter__(self):
        if self.id:
            self._session = APublishSession(self.id, client=self.client)
        else:
            self._session = APublishSession.create(
                entity_id=self._task_id,
                name=self.publication_name,
                version=self.publication_version,
                comment=self._kwargs.get('comment', ''),
                client=self.client,
            )
            self._set_id(self._session.id)
        self.set_status(self.STATUS.IN_PROGRESS)
        self.__is_context_manager_opened = True
        emit('pipe.publish.publish_process_started', {'session': self})

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__is_context_manager_opened = False
        if exc_type:
            self.on_error(exc_val)
            return False
        else:
            return self.on_success()

    def set_dry_run(self, dry_run: bool) -> None:
        self._dry_run = dry_run

    def __str__(self):
        return self.id

    def __repr__(self):
        return f'{self.__class__.__name__}({self.id})'

    def _init_session_data(self, session_id: str = None) -> defaultdict:
        session_data = deep_tree()
        if session_id is not None:
            self._set_id(session_id)
            data = self.store_helper.load()
            self.id = data.pop('id')
            session_data.update(data)
            if session_data['instances']:
                session_data['instances'] = {
                    inst_id: inst.PublishInstance.from_dict(data)
                    for inst_id, data in session_data['instances'].items()
                }
            return session_data
        else:
            return session_data

    def _init_settings(self, workspace_id: str|None = None) -> WorkspaceSettingsHub:
        if workspace_id is None:
            return self.task.project.get_settings()
        else:
            ws = AWorkspace(workspace_id, client=self.client)
            return ws.get_current_revision().get_settings()

    @property
    def publication_version(self) -> int:
        if 'publication_version' not in self._data:
            self._data['publication_version'] = APublishSession.get_next_version(self._task_id, client=self.client)
        return self._data['publication_version']

    @property
    def publication_name(self):
        if 'publication_name' not in self._data:
            self._data['publication_name'] = self.create_name()
        return self._data['publication_name']

    @property
    def published_versions(self):
        return self._versions

    def create_name(self):
        template = self.settings.get('agio_pipe.publication_name_template')
        templates = {
            'default': template
        }
        context = self.get_session_context()
        solver = template_solver.TemplateSolver(templates)
        solved_name = solver.solve('default', context)
        return solved_name

    @cached_property
    def client(self):
        return self._kwargs.get('client')

    @cached_property
    def task(self):
        return ATask(self._task_id, client=self.client)

    def get_session_context(self) -> dict:
        return {
            'publication_entity': AEntity.from_id(self._task_id, client=self.client),
            'publication_version': self.publication_version,
        }

    def serialize(self):
        return self.to_dict()

    def to_dict(self) -> dict:

        def entity_encode(obj):
            if hasattr(obj, 'serialize'):
                return obj.serialize()
            raise TypeError(f'Cant serialize to dict: {type(obj)} {obj}')

        return {
            'id': self.id,
            'task_id': self._task_id,
            **to_simple_dict(self._data, entity_encode)
        }

    def dump(self) -> Path|None:
        if self._dry_run:
            return None
        data = self.serialize()
        return self.store_helper.dump(data)

    ###########################################################

    def set_status(self, status: STATUS) -> None:
        self._data['status'] = status
        self.dump()
        self._session.update(state=status)

    @property
    def status(self):
        return self._data.get('status') or self.STATUS.PENDING

    def on_error(self, error: Union[str, type[BaseException]]) -> None:
        if self.delete_on_error:
            self._session.delete()
        else:
            err = {
                'message': str(error),
            }
            if isinstance(error, Exception):
                err['traceback'] = ''.join(traceback.format_exception(error))
            self._data['error'] = err
            self.set_status(self.STATUS.FAILED)
            self._dump_to_db()
        emit('pipe.publish.publish_process_failed', {'session': self})

    def on_success(self):
        # TODO check versions exists
        self.set_status(self.STATUS.DONE) # TODO user SYNC status by default
        self._dump_to_db()
        emit('pipe.publish.publish_process_done', {'session': self})
        return True

    def create_versions(self, instances: list[PublishInstance]) -> list[AVersion]:
        """Create versions in database"""
        if not self.__is_context_manager_opened:
            raise PublishError('Session context manager is not opened')
        if not instances:
            raise PublishError('No instances to create versions')
        created: list[tuple[AVersion, PublishInstance]] = []
        for instance in instances:
            if not instance.get_value('product_outputs'):
                raise PublishError(f'Instance has no product outputs {instance}')
        try:
            for instance in instances:
                version, files = create_product_version(
                    product_id=instance.product.id,
                    task_id=instance.task.id,
                    version=instance.version,
                    project_files=instance.get_value('product_outputs'),
                    publish_session_id=self.id
                )
                instance.set_results(version, files)
                created.append((version, instance))
        except Exception:
            logger.error(
                'Failed to create new version. Early created versions in current session will be deleted.')
            for version, instance in created:
                version.delete()
            raise
        for version, instance in created:
            emit('pipe.publish.version_created', {
                'version': version,
                'instance': instance,
                'session': self
            })
            logger.info('Created new version: %s', repr(version))
        self._versions = [x[0] for x in created]
        return self._versions

    def _dump_to_db(self):
        if self._dry_run:
            return
        if self._session:
            ###
            print(' Dump data '.center(150, '='))
            print(json.dumps(self.serialize(), indent=1))
            print('='*150)
            ###
            # TODO: add logs and data
            self.set_status(self.status)
        else:
            logger.error('Session instance not created')

    @property
    def data(self):
        return self._data

    def set_value(self, key: str, value: Any) -> None:
        self._data['context'][key] = value

    def get_value(self, key: str, default: Any = None) -> Any:
        return self._data['context'].get(key, default)

    @property
    def context(self):
        return dict(self._data.get('context', {}))

    @property
    def instances(self) -> dict[str, inst.PublishInstance]:
        return dict(self._data.get('instances', {}))

    def add_instance(self, instance: inst.PublishInstance):
        if not isinstance(instance, inst.PublishInstance):
            raise TypeError(f"Instance object must be typeinstance.PublishInstance, not {type(instance)}")
        if instance.id in self.instances:
            raise ValueError(f"Instance with ID {instance.id} already exists")
        if instance in self.instances.values():
            raise ValueError(f"Instance with same product and task already exists: {instance}")
        self._data['instances'][instance.id] = instance
        emit('pipe.publish.instance_added', {'instance': instance, 'session': self})
        return instance

    def remove_instance(self, instance_id: UUID |inst.PublishInstance | str):
        if isinstance(instance_id, inst.PublishInstance):
            instance_id = instance_id.id
        elif isinstance(instance_id, UUID):
            instance_id = str(instance_id)

        if instance_id not in self.instances:
            raise ValueError(f"Instance {instance_id} not registered")
        del self.instances[instance_id]

    def get_instance(self, instance_id: UUID | str) -> inst.PublishInstance | None:
        if isinstance(instance_id, UUID):
            instance_id = str(instance_id)
        return self.instances.get(instance_id)

    def has_instance(self, instance_id: UUID | str | inst.PublishInstance) -> bool:
        if isinstance(instance_id, UUID):
            instance_id = str(instance_id)
        elif isinstance(instance_id, inst.PublishInstance):
            instance_id = instance_id.id
        return self.instances.get(instance_id) is not None

    def get_instance_by_name(self, name: str) -> inst.PublishInstance | None:
        for inst in self.instances.values():
            if inst.name == name:
                return inst
        return None

    def iter_instances(self) -> Generator[inst.PublishInstance, None, None]:
        yield from self.instances.values()

    @property
    def tempdir(self) -> Path:
        return Path(tempfile.gettempdir(), self.id)
