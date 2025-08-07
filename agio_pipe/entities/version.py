from typing import Self, Iterator
from agio.core import api
from agio.core.domains import DomainBase


class AVersion(DomainBase):
    type_name = "version"

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.pipe.get_version(object_id)

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

