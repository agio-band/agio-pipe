from __future__ import annotations

import uuid
from abc import abstractmethod, ABC
from functools import cache
from typing import Any

from agio.tools.json_serializer import to_simple_dict
from agio.core.entities import task as task_, product as product_


class ExportContainerBase(ABC):
    def __init__(self, scene_object: Any, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene_object = scene_object

    @classmethod
    def create(cls,
               name: str,
               task: task_.ATask,
               product: product_.AProduct,
               sources: list[Any] = None,
               container_id: str = None
        ) -> Any:
        scene_obj = cls.create_scene_object(name)
        container = cls(scene_obj)
        container.set_task(task)
        container.set_product(product)
        container.set_id(container_id or str(uuid.uuid4()))
        if sources:
            for src in sources:
                container.add_source(src)
        return container

    def __str__(self):
        product = self.get_product()
        if product:
            return f'{self.name}: {product.name}.{product.variant}'
        else:
            return f'{self.name}: ---.---'

    def __repr__(self):
        return f'<Container [{self}]>'

    def __eq__(self, other):
        my_product, my_task = self.get_product(), self.get_task()
        other_product, other_task = other.get_product(), other.get_task()
        if not all([my_product, other_product, my_task, other_task]):
            return False
        return my_product.id == other_product.id and my_task.id == other_task.id

    @cache
    def __hash__(self):
        product, task = self.get_product(), self.get_task()
        task_id = task.id if task else ''
        product_id = product.id if product else ''
        return hash(f"{task_id}{product_id}")

    @property
    @abstractmethod
    def name(self) -> str:
        """Get container name"""

    @property
    @abstractmethod
    def id(self) -> str:
        """Get container ID"""

    @abstractmethod
    def set_id(self, value: str):
        """Set container ID"""

    @abstractmethod
    def validate(self, data: dict) -> None:
        """
        Local validation implementation
        """

    @classmethod
    @abstractmethod
    def create_scene_object(cls, name: str, container_id: str = None) -> Any:
        """
        Implementation for current software
        """

    @abstractmethod
    def add_source(self, value: str):
        """
        Add source object to the container
        """

    @abstractmethod
    def remove_source(self, value: str):
        """
        Remove source from container
        """

    @abstractmethod
    def get_sources(self) -> list[str]:
        """
        Read source object or objects from the container
        """

    @abstractmethod
    def set_product(self, product_type: product_.AProduct):
        """
        Save product type to the container
        """

    @abstractmethod
    def get_product(self) -> product_.AProduct:
        """
        Read product type from the container
        """

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """
        Get depend publish version ids
        """

    @abstractmethod
    def set_task(self, task: task_.ATask):
        """
        Save task to the container
        """

    @abstractmethod
    def get_task(self) -> task_.ATask:
        """
        Read task from the container
        """

    @abstractmethod
    def set_options(self, options: dict):
        """Save custom options to the container"""

    @abstractmethod
    def get_options(self) -> dict:
        """Read custom options from the container"""

    def to_dict(self) -> dict:
        """Serialize scene object to dict"""
        data = self._base_validate()
        self.validate(data)

        def default_serializer(obj):
            if hasattr(obj, 'to_dict'):
                return obj.to_dict()
            raise TypeError

        return to_simple_dict(data, default_serializer)

    def _base_validate(self) -> dict:
        """
        Check container fields and validate objects in scene
        """
        fields = self.__dump_dict()
        for field in ('id', 'name', 'sources', 'task_id', 'product_id'):
            if fields.get(field) is None:
                raise ValueError('Field "%s" must be set' % field)
        return fields

    def __dump_dict(self):
        product = self.get_product()
        task = self.get_task()

        return dict(
            id=self.id,
            name=self.name,
            sources=self.get_sources(),
            task_id=task.id,
            product_id=product.id,
            # optional fields
            options=self.get_options(),
            # extra fields
            product_type=product.type.name,
            product_type_id=product.type.id,
            product_name=product.name,
            variant=product.variant,
            task_name=task.name
        )
