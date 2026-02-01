from abc import ABC, abstractmethod
from typing import Iterable, Generator

from agio_pipe.base_classes.export_container import ExportContainerBase
from agio_pipe.entities import product as product_entity
from agio_pipe.entities.task import ATask
from agio_pipe.exceptions import DuplicateError


class PublishSceneBase(ABC):
    """
    Manage export containers in current app scene
    """
    export_container_class = None

    def __init__(self):
        self.scene_file = None

    def __str__(self) -> str:
        return f"{self.__class__.__name__}"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"

    @abstractmethod
    def save(self, file: str) -> str:
        ...

    @abstractmethod
    def load(self, file: str) -> str:
        ...

    def get_export_container_class(self):
        return self.export_container_class

    def create_container(
            self,
            name:str,
            task: ATask,
            product: product_entity.AProduct,
            sources: list[str] = None,
            id: str = None,
        ) -> ExportContainerBase:
        if not isinstance(sources, Iterable):
            raise TypeError("Sources must be a list")
        cont_cls = self.get_export_container_class()
        cont = cont_cls.create(name=name, task=task, product=product, sources=sources)#, id=id)
        self.create_scene_container(cont)
        return cont

    @abstractmethod
    def create_scene_container(self, container: ExportContainerBase):
        ...

    def _validate_duplicate(self, container: ExportContainerBase):
        if self.find_container_in_scene(container.id) is not None:
            raise DuplicateError(container.id)

    @abstractmethod
    def remove_scene_container(self, container_id: str) -> ExportContainerBase|None:
        ...

    @abstractmethod
    def iter_scene_containers(self) -> Generator[ExportContainerBase, None, None]:
        ...

    def get_scene_containers_dict(self):
        return [cont.to_dict() for cont in self.get_scene_containers()]

    def get_scene_containers(self) -> tuple[ExportContainerBase, ...]:
        return tuple(self.iter_scene_containers())


    def find_container_in_scene(self, container_id: str) -> ExportContainerBase|None:
        for cont in self.iter_scene_containers():
            if cont.id == container_id:
                return cont
        return None
