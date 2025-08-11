from typing import Self, Iterator
from uuid import UUID

from agio.core import api
from agio.core.domains import DomainBase
from agio_pipe.entities import product


class AVersion(DomainBase):
    domain_name = "version"

    @property
    def version_number(self):
        return int(self._data['name'])

    def get_product(self):
        return product.AProduct(self.data['publish']['id'])

    @classmethod
    def get_data(cls, object_id: str) -> dict:
        return api.pipe.get_version(object_id)

    def update(self, fields: dict) -> None:
        return api.pipe.update_version(self.id, fields)

    @classmethod
    def iter(cls, entity_id: str|UUID, product_type: str = None, variant: str = None) -> Iterator[Self]:
        for data in api.pipe.iter_prodict_versions(entity_id, product_type, variant):
            yield AVersion(data)

    @classmethod
    def get_next_version_number(cls, task_id: str, product_id: str) -> int:
        return api.pipe.get_next_version_number(task_id, product_id)

    @classmethod
    def create(cls,
               product_id: str|UUID,
               task_id: str|UUID,
               fields: dict,
               version_number: int = None,
        ) -> Self:
        if version_number is None:
            version_number = cls.get_next_version_number(task_id, product_id)
        if 'files' not in fields:
            raise ValueError('Version files not specified')
        version_id = api.pipe.create_version(str(version_number), product_id, task_id, fields)
        return AVersion(version_id)

    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    def find(cls, **kwargs):
        raise NotImplementedError()

    def get_task(self):
        from agio_pipe.entities.task import ATask

        task = ATask.get_data(self._data['entityId'])
        return ATask(task)

    def to_dict(self):
        return dict(
            id=self.id,
            entity=self._data['entity'],
            fields=self._data['fields'],
            version=self.version_number,
            product=self.get_product().to_dict(),
        )