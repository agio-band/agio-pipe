from typing import Iterator
from uuid import UUID

from agio.core import api
from agio.core.entities import DomainBase


class AProductType(DomainBase):
    domain_name = "product_type"

    @classmethod
    def get_data(cls, object_id: str | UUID) -> dict:
        return api.pipe.get_product_type(object_id)

    def update(self, config: dict = None, data_type: str = None) -> None:
        return api.pipe.update_product_type(
            self.id,
            config=config,
            data_type=data_type,
        )

    def set_config(self, config: dict) -> None:
        return self.update(config=config)

    @classmethod
    def iter(cls, **kwargs) -> Iterator['AProductType']:
        for prod in api.pipe.iter_product_types(**kwargs):
            yield prod

    @classmethod
    def create(cls,
               name: str,
               description: str,
               config: dict = None,
               data_type: str = None,
               ) -> 'AProductType':
        product_type_id = api.pipe.create_product_type(
            name, description, config, data_type)
        return cls(product_type_id)

    def delete(self) -> None:
        raise NotImplementedError

    @classmethod
    def find(cls,
             name: str,
             **kwargs):
        data = api.pipe.get_product_type_by_name(name)
        if not data:
            return
        return cls(data)

    @property
    def name(self) -> str:
        return self._data["name"]

    @property
    def data_type(self) -> str:
        return self._data["dataType"]

    @property
    def config(self) -> dict:
        return self._data["config"]





