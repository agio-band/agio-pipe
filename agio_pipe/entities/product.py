from __future__ import annotations
from typing import Iterator
from uuid import UUID

from agio.core import api
from agio.core.entities import DomainBase, AEntity
from . import product_type


class AProduct(DomainBase):
    domain_name = "product"

    @classmethod
    def get_data(cls, object_id: str | UUID) -> dict:
        return api.pipe.get_product(object_id)

    def update(self, **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def iter(cls,
             entity: str | UUID | AEntity,
             product_type_id: str = None,
             product_type_name: str = None,
             **kwargs) -> Iterator['AProduct']:
        if isinstance(entity, AEntity):
            entity = str(entity.id)
        for prod in api.pipe.iter_products(
                entity_id=entity,
                product_type_id=product_type_id,
                product_type_name=product_type_name
            ):
            yield cls(prod)

    @classmethod
    def create(cls,
               entity_id: str | UUID,
               name: str,
               product_type_id: str,
               variant: str,
               fields: dict = None,
               ) -> 'AProduct':
        product_id = api.pipe.create_product(name, entity_id, variant, product_type_id=product_type_id, fields=fields)
        return cls(product_id)

    def delete(self) -> None:
        raise NotImplementedError

    @classmethod
    def find(cls,
             entity_id: str | UUID,
             name: str,
             variant: str = None,
             **kwargs):
        data = api.pipe.find_product(entity_id=entity_id, name=name, variant=variant)
        if not data:
            return
        return cls(data)

    @property
    def name(self) -> str:
        return self._data["name"]

    @property
    def variant(self) -> str:
        return self._data["variant"]

    @property
    def type(self) -> product_type.AProductType:
        return product_type.AProductType(self._data["type"])

    @property
    def entity(self) -> AEntity:
        entity_data = api.track.get_entity(self._data["entityId"])
        return AEntity.from_data(entity_data)





