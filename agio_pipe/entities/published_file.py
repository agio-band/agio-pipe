from typing import Self, Iterator
from uuid import UUID

from agio.core.domains import DomainBase
from agio.core import api
from agio_pipe.entities.version import AVersion


class APublishedFile(DomainBase):
    domain_name = "published_file"

    @property
    def name(self):
        return self._data.get("name")

    @property
    def path(self):
        return self._data.get("path")

    def get_version(self) -> AVersion:
        return AVersion(self._data.get("publishVersionId"))

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.pipe.get_published_file(object_id)

    def update(self, **kwargs) -> None:
        raise NotImplementedError()

    @classmethod
    def iter(cls, version_id: str|UUID) -> Iterator[Self]:
        yield from api.pipe.iter_publish_files(version_id=version_id)

    @classmethod
    def create(cls, version_id: str|UUID, path: str, name: str = None) -> Self:
        data = api.pipe.create_publish_file(version_id=version_id, path=path, name=name)
        return APublishedFile(data)

    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    def find(cls, version_id: str, name: str = None, path: str = None, use_regex_filter=False):
        yield from api.pipe.iter_publish_files(
            version_id=version_id,
            path=path,
            name=name,
            use_regex=use_regex_filter,
        )

