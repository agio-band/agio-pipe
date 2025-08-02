from functools import cached_property
from typing import Self, Iterator

from agio.core.domains import AEntity


class ATask(AEntity):
    type_name = "task"
    entity_class = "Task"

    @classmethod
    def get_data(cls, entity_id: str) -> dict:
        pass

    def update(self, **kwargs) -> None:
        pass

    @classmethod
    def iter(cls, **kwargs) -> Iterator[Self]:
        pass

    @classmethod
    def create(cls, **kwargs) -> Self:
        pass

    def delete(self) -> None:
        pass

    @classmethod
    def find(cls, **kwargs):
        pass

    @property
    def entity_id(self) -> str:
        return '???'

    @property
    def entity_type(self) -> str:
        return '???'

    @cached_property
    def entity(self) -> AEntity:
        return '???'
