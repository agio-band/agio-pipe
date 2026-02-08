from __future__ import annotations

import json
from pathlib import Path
from typing import Generator, Type

from agio.core import chips
from agio_pipe.base_classes.export_container import ExportContainerBase
from agio_pipe.base_classes.publish_scene import PublishSceneBase
from agio_pipe.chips.publish_scene.export_container import ExportContainer
from agio_pipe.entities import product as product_entity
from agio_pipe.entities.task import ATask
from agio_pipe.exceptions import DuplicateError
from agio_pipe.publish.instance import PublishInstance


@chips.register('publish_scene', 'default')
class StandalonePublishScene(PublishSceneBase):
    export_container_class = ExportContainer

    def __init__(self,):
        super().__init__()
        self.containers: dict[str, ExportContainer] = {}

    def load(self, file: str|Path) -> None:
        file = Path(file).expanduser()
        with file.open("r") as f:
            json_data = json.load(f)
        self.load_from_dict(json_data)

    def load_from_dict(self, data: dict) -> None:
        for data in data["containers"]:
            container = ExportContainer(data)
            # self.add_container(container)
            self.containers[container.id] = container

    def save(self, file: str) -> str:
        file = Path(file).expanduser()
        file.parent.mkdir(parents=True, exist_ok=True)
        with file.open("w") as f:
            json.dump({
                'containers': self.get_containers_dict()
            }, f, indent=2)
        return file.as_posix()

    def create_container(
            self,
            name:str,
            task: ATask,
            product: product_entity.AProduct,
            sources: list[str] = None,):
        cont = super().create_container(name, task, product, sources)
        self.add_container(cont)

    def add_container(self, container: ExportContainerBase):
        if container in self.containers.values():
            raise DuplicateError(detail='Container with same parameters already exists')
        self.containers[container.id] = container

    def remove_container(self, container_id: str) -> ExportContainerBase | None:
        self.containers.pop(container_id, None)

    def iter_containers(self) -> Generator[ExportContainerBase, None, None]:
        yield from iter(self.containers.values())
