from abc import ABC, abstractmethod
from typing import Any

from agio.core.domains import AProductType, ATask, AProductVersion


class ExportContainerBase(ABC):
    def __init__(self, scene_container: Any):
        self.obj = scene_container

    @classmethod
    def create(cls,
               source_object: Any,
               product_type: AProductType,
               task: ATask,
               ) -> Any:
        container = cls.create_scene_container()
        instance = cls(container)
        instance.add_source(source_object)
        instance.set_product_type(product_type)
        instance.set_task(task)
        return instance

    @abstractmethod
    def validate(self):
        """
        Check container fields and validate objects in scene
        """

    @classmethod
    @abstractmethod
    def create_scene_container(cls):
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
    def set_product_type(self, product_type: AProductType):
        """
        Save product type to the container
        """

    @abstractmethod
    def get_product_type(self) -> AProductType:
        """
        Read product type from the container
        """

    @abstractmethod
    def set_variant(self, variant: AVariant|UUID|str):
        """
        Save variant type to the container
        """

    @abstractmethod
    def get_variant(self) -> AVariant:
        """
        Read variant type from the container
        """

    @abstractmethod
    def set_task(self, task: ATask):
        """
        Save task to the container
        """

    @abstractmethod
    def get_task(self) -> ATask:
        """
        Read task from the container
        """

    @abstractmethod
    def set_comment(self, text: str):
        """"""

    @abstractmethod
    def get_comment(self) -> str:
        """"""

    @abstractmethod
    def set_options(self, options: dict):
        """"""

    @abstractmethod
    def get_options(self) -> dict:
        """"""

    def to_dict(self) -> dict:
        return dict(
            source_object=self.get_sources(),
            task=self.get_task(),
            product_type=self.get_product_type(),
            variant=self.get_variant(),
            options=self.get_options(),
            comment=self.get_comment(),
        )

