from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any

from agio_pipe.entities import product as product_
from agio_pipe.entities.task import ATask


class ExportContainerBase(ABC):
    def __init__(self, scene_container: Any):
        self.obj = scene_container

    @classmethod
    def create(cls,
               name: str,
               task: 'ATask',
               product: product_.AProduct,
               source_objects: list[Any] = None
               ) -> Any:
        container = cls.create_scene_container(name)
        instance = cls(container)
        instance.set_task(task)
        instance.set_product(product)
        if source_objects:
            for src in source_objects:
                instance.add_source(src)
        return instance

    def __str__(self):
        product = self.get_product()
        if product:
            return f'{self.name}: {product.name}.{product.variant}'
        else:
            return f'{self.name}: ---.---'

    def __repr__(self):
        return f'<Container [{self}]>'

    # @property
    # @abstractmethod
    # def id(self):
    #     """Unique container ID"""

    @property
    @abstractmethod
    def name(self):
        """Container name"""

    def validate(self):
        """
        Local validation implementation
        """

    def _base_validate(self):
        """
        Check container fields and validate objects in scene
        """
        for field in ('id', 'name', 'sources', 'task', 'product'):
            if self.obj.get(field) is None:
                raise ValueError('%s must be set' % field)

    @classmethod
    @abstractmethod
    def create_scene_container(cls, name: str):
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
    def get_sources(self):
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
    def set_task(self, task: 'ATask'):
        """
        Save task to the container
        """

    @abstractmethod
    def get_task(self) -> 'ATask':
        """
        Read task from the container
        """

    @abstractmethod
    def set_options(self, options: dict):
        """"""

    @abstractmethod
    def get_options(self) -> dict:
        """"""

    def to_dict(self) -> dict:
        self._base_validate()
        self.validate()
        product = self.get_product()
        task = self.get_task()
        # TODO: use Pydantic
        return dict(
            # id=self.id,
            name=self.name,
            sources=self.get_sources(),
            task_id=task.id,
            product_id=product.id,
            options=self.get_options(),
            # extra fields
            product_type=product.type,
            product_name=product.name,
            variant=product.variant,
            task_name=task.name
        )

    def __eq__(self, other):
        my_product, my_task = self.get_product(), self.get_task()
        other_product, other_task = other.get_product(), other.get_task()
        if not all([my_product, other_product, my_task, other_task]):
            return False
        return my_product.id == other_product.id and my_task.id == other_task.id

    def __hash__(self):
        product, task = self.get_product(), self.get_task()
        task_id = task.id if task else ''
        product_id = product.id if product else ''
        return hash(f"{task_id}{product_id}")
