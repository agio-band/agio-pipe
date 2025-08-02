import uuid
from dataclasses import dataclass, field, InitVar
from typing import Any

from agio.core.domains import AProductType, AEntity
from agio.core.domains.variant import AVariant
from agio_pipe.entities.task import ATask


@dataclass
class PublishInstance:
    # init values
    task_id: InitVar[str]
    product_type_id: InitVar[str]
    variant_id: InitVar[str]
    # required
    sources: list[str]
    # optional
    id: str = uuid.uuid4().hex
    name: str = None
    options: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    # post creation values
    task: ATask = field(init=False)
    entity: AEntity = field(init=False)
    product_type: AProductType = field(init=False)
    variant: AVariant = field(init=False)

    def __post_init__(self, task_id: str|ATask, product_type_id: str|AProductType, variant_id: str|AVariant):
        # self.task = ATask(task_id) if isinstance(task_id, str) else task_id
        self.task = type('ATask', (object,), {'id': task_id, 'entity': type('Entity', (object,), {'id': '123', 'name': 'asset1', 'type': 'asset'})()})()
        self.entity = self.task.entity
        # self.product_type = AProductType(product_type_id) if isinstance(product_type_id, str) else product_type_id
        self.product_type = type('AProductType', (object,), {'id': task_id, 'name': 'workfile'})()
        # self.variant = AVariant(variant_id) if isinstance(variant_id, str) else variant_id
        self.variant = type('AVariant', (object,), {'id': task_id, 'name': 'main'})()
        if not self.name:
            self.name = f'{self.entity.type}_{self.product_type.name}_{self.variant.name}'

    def to_dict(self):
        return dict(
            id=self.id,
            name=self.name,
            task_id=self.task.id,
            product_type_id=self.product_type.id,
            variant_id=self.variant.id,
            sources=self.sources,
            options=self.options,
            metadata=self.metadata,
        )

    def __eq__(self, other):
        return all([
            self.task.id == other.task.id,
            self.product_type.id == other.product_type_id,
            self.variant.id == other.variant,
        ])

    @property
    def project(self):
        return