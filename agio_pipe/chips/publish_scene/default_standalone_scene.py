from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable, Generator

from agio_pipe.base_classes.export_container import ExportContainerBase
from agio_pipe.base_classes.publish_scene import PublishSceneBase
from agio_pipe.exceptions import DuplicateError
from agio_pipe.chips.publish_scene.export_container import ExportContainer
from agio.core import chips


@chips.register('publish_scene', 'default')
class StandalonePublishScene(PublishSceneBase):
    export_container_class = ExportContainer

    def __init__(self, scene_file: str|dict = None):
        super().__init__(scene_file)
        self.containers: dict[str, ExportContainer] = {}
        if isinstance(scene_file, (str, Path)):
            self.load(scene_file)
        elif isinstance(scene_file, dict):
            self.load_from_dict(scene_file)

    def load(self, file) -> None:
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
                'containers': self.get_scene_containers_dict()
            }, f, indent=2)
        return file.as_posix()

    def create_scene_container(self, container: ExportContainer):
        if container in self.containers.values():
            raise DuplicateError(detail='Container with same parameters already exists')
        self.containers[container.id] = container

    def remove_scene_container(self, container_id: str) -> ExportContainerBase | None:
        self.containers.pop(container_id, None)

    def iter_scene_containers(self) -> Generator[ExportContainerBase, None, None]:
        yield from iter(self.containers.values())
