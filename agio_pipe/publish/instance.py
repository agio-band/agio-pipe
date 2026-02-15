from __future__ import annotations

import uuid
from typing import Any

from agio.core.entities import DomainBase
from agio_pipe.base_classes.export_container import ExportContainerBase
from agio_pipe.entities import version as vers
from agio_pipe.entities.product import AProduct
from agio_pipe.entities.task import ATask


class PublishInstance:
    def __init__(
            self,
            task: str|ATask,
            product: AProduct,
            sources: list[str],
            name: str = None,
            id: str = None,
            options: dict[str, Any] = None,
            dependencies: list[str] = None,
            data: dict[str, Any] = None
        ):
        self.id = id or uuid.uuid4().hex
        self.task = ATask(task) if isinstance(task, (str, uuid.UUID)) else task
        self.product = AProduct(product) if isinstance(product, (str, uuid.UUID)) else product
        self.name = name or f'{self.task.entity.name}_{self.task.name}_{self.product.name}_{self.product.variant}'
        self.sources = sources or []
        self.options = options or {}
        self.dependencies = dependencies or []
        self.data = data or {}
        self._version = None
        self._results = {}
        self._enabled = True

    def set_value(self, key: str, value: Any):
        self.data[key] = value

    def get_value(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    @property
    def version(self):
        if self._version is None:
            self._version = vers.AVersion.get_next_version_number(self.product.id)
        return self._version

    def set_version(self, version: int):
        self._version = version

    def serialize(self) -> dict[str, Any]:
        data = dict(
            id=self.id,
            name=self.name,
            task_id=self.task.id,
            product_id=self.product.id,
            sources=self.sources,
            options=self.options,
            data=self.data,
            version=self._version,
            enabled=self._enabled,
        )
        if self._results:
            data['results'] = self._results
        return data

    @classmethod
    def from_dict(cls, instance_data: dict[str, Any]) -> PublishInstance:
        # restore entities from dicts in data
        inst_data = {}
        instance_data['data'] = instance_data.get('data') or {}
        for k, v in instance_data['data'].items():
            if isinstance(v, dict) and '_' in v:
                inst_data[k] = DomainBase.deserialize(v)
            else:
                inst_data[k] = v
        inst = PublishInstance(
            id=instance_data['id'],
            task=ATask(instance_data['task_id']),
            product=AProduct(instance_data['product_id']),
            sources=instance_data['sources'],
            name=instance_data['name'],
            options=instance_data.get('options') or {},
            dependencies=instance_data.get('dependencies') or [],
            data=inst_data,
        )
        if 'version' in instance_data:
            inst.set_version(instance_data['version'])
        if 'results' in instance_data:
            inst.set_results(**instance_data['results'])
        if 'enable' in instance_data:
            if not instance_data['enable']:
                inst.disable()
        return inst

    @classmethod
    def from_export_container(cls, container: ExportContainerBase) -> PublishInstance:
        return cls(
            task=container.get_task(),
            product=container.get_product(),
            sources=container.get_sources(),
            name=container.name,
            options=container.get_options(),
            dependencies=container.get_dependencies()
            # metadata
            # data
        )

    def set_results(self, new_version: vers.AVersion, published_files: list):
        if isinstance(new_version, dict):
            new_version = DomainBase.deserialize(new_version)
        self._results = dict(
            new_version=new_version,
            published_files=published_files
        )

    def get_results(self):
        return self._results

    def disable(self):
        self._enabled = False

    def enable(self):
        self._enabled = True

    @property
    def enabled(self):
        return self._enabled

    def __eq__(self, other):
        return all([
            self.task.id == other.task.id,
            self.product.id == other.product.id,
        ])

    def __hash__(self):
        return hash(f'{self.task.name}{self.product.name}{self.product.variant}')

    def __repr__(self) -> str:
        return f'<Instance {self.task.name}/{self.product.name}.{self.product.variant}>'

    @property
    def project(self):
        return self.task.project

