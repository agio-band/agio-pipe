from __future__ import annotations
import uuid
from dataclasses import dataclass, field, InitVar
from typing import Any, TYPE_CHECKING

from agio_pipe.entities import version

if TYPE_CHECKING:
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
            metadata: dict[str, Any] = None
        ):
        self.id = id or uuid.uuid4().hex
        self.task = ATask(task) if isinstance(task, (str, uuid.UUID)) else task
        self.product = AProduct(product) if isinstance(product, (str | uuid.UUID)) else product
        self.name = name or f'{self.task.entity.name}_{self.task.name}_{self.product.name}_{self.product.variant}'
        self.sources = sources or []
        self.options = options or {}
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self._version = None

    @property
    def version(self):
        if self._version is None:
            self._version = version.AVersion.get_next_version_number(self.task.id, self.product.id)
        return self._version

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            task_id=self.task.id,
            product_id=self.product.id,
            sources=self.sources,
            options=self.options,
            metadata=self.metadata,
        )

    def __eq__(self, other):
        return all([
            self.task.id == other.task.id,
            self.product.id == other.product.id,
        ])

    def __repr__(self) -> str:
        return f'<Instance {self.task.name}/{self.product.type}.{self.product.variant}>'

    @property
    def project(self):
        return self.task.project
