from __future__ import annotations

import json
import logging
import tempfile
import traceback
from collections import defaultdict
from enum import StrEnum
from pathlib import Path
from typing import Any, Generator, Union
from uuid import uuid4, UUID

from agio.core.entities import AWorkspace
from agio.core.entities.publish_session import APublishSession
from agio.core.events import emit
from agio.core.settings.settings_hub import WorkspaceSettingsHub
from agio.tools import local_dirs
from agio.tools.data_helpers import deep_tree
from agio.tools.json_serializer import to_simple_dict
from . import instance as inst

logger = logging.getLogger(__name__)


class PublishSession:
    store_path = Path(local_dirs.cache_dir('publish_sessions'))

    class STATUS(StrEnum):
        PENDING = 'PENDING'
        IN_PROGRESS = 'IN_PROGRESS'
        DONE = 'DONE'
        FAILED = 'FAILED'
        CANCELED = 'CANCELED'
        SYNC = 'SYNC'

    def __init__(self, task_id: str|UUID, session_id: str = None, workspace_id: str = None, **kwargs) -> None:
        self._kwargs = kwargs
        self._task_id = task_id
        self.id: str = session_id
        self._data: dict = self._init_session_data(session_id)
        self.settings = self._init_settings(workspace_id)
        self._dry_run = False
        self._session: APublishSession|None = None

    def __enter__(self):
        if self.id:
            self._session = APublishSession(self.id)
        else:
            self._session = APublishSession.create(entity_id=self._task_id, comment=self._kwargs.get('comment', ''))
            self.id = self._session.id
        self.set_status(self.STATUS.IN_PROGRESS)
        emit('pipe.publish.publish_process_started', {'session': self._session})

    def __exit__(self, exc_type, exc_val, exc_tb):
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
        if session_id is None:
            return session_data
        else:
            data = self._load_from_file(session_id)
            self.id = data.pop('id')
            session_data.update(data)
            if session_data['instances']:
                session_data['instances'] = {
                    inst_id: inst.PublishInstance.from_dict(data)
                    for inst_id, data in session_data['instances'].items()
                }
            return session_data

    def _init_settings(self, workspace_id: str) -> WorkspaceSettingsHub:
        if workspace_id is None:
            ws = AWorkspace.current()
        else:
            ws = AWorkspace(workspace_id)
        return ws.get_current_revision().get_settings()

    def serialize(self):
        return self.to_dict()

    def to_dict(self) -> dict:

        def entity_encode(obj):
            if hasattr(obj, 'serialize'):
                return obj.serialize()
            raise TypeError(f'Cant serialize to dict: {type(obj)} {obj}')
        return {
            'id': self.id,
            **to_simple_dict(self._data, entity_encode)
        }

    def dump(self) -> Path|None:
        if self._dry_run:
            return None
        data = self.serialize()
        session_path = self.session_file(self.id)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        with session_path.open('w') as session_file:
            json.dump(data, session_file, indent=2, ensure_ascii=False)
        return session_path

    @classmethod
    def load(cls, session_id: str = None) -> PublishSession:
        session = cls(session_id)
        return session

    @classmethod
    def _load_from_file(cls, instance_id: str):
        session_path = cls.session_file(instance_id)
        if not session_path.exists():
            raise FileNotFoundError(f"Session file not found: {session_path}")
        with open(session_path) as session_file:
            session_dict = json.load(session_file)
        return session_dict

    @classmethod
    def session_file(cls, session_id: str) -> Path:
        return cls.store_path.joinpath(session_id).with_suffix('.json')

    @property
    def dump_file(self):
        if not self.id:
            raise ValueError('Session instance not initialized yet. No id value.')
        return self.session_file(self.id)

    ###########################################################

    def set_status(self, status: STATUS) -> None:
        self._data['status'] = status
        self.dump()
        self._session.update(state=status)

    @property
    def status(self):
        return self._data.get('status') or self.STATUS.PENDING

    def on_error(self, error: Union[str, type[BaseException]]) -> None:
        err = {
            'message': str(error),
        }
        if isinstance(error, Exception):
            err['traceback'] = ''.join(traceback.format_exception(error))
        self._data['error'] = err
        self.set_status(self.STATUS.FAILED)
        self._dump_to_db()
        emit('pipe.publish.publish_process_failed', {'session': self._session})

    def on_success(self):
        # TODO check versions exists
        self.set_status(self.STATUS.DONE) # TODO user SYNC status by default
        self._dump_to_db()
        emit('pipe.publish.publish_process_done', {'session': self._session})
        return True

    def _dump_to_db(self):
        if self._dry_run:
            return
        if self._session:
            ###
            from pprint import pprint
            print(' Dump data '.center(150, '='))
            pprint(self._data)
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
