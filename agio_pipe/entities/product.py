from typing import Iterator
from uuid import UUID

from agio.core import api
from agio.core.domains import DomainBase, AEntity
from . import product_type


class AProduct(DomainBase):
    domain_name = "product"

    @classmethod
    def get_data(cls, object_id: str | UUID) -> dict:
        return api.pipe.get_product(object_id)

    def update(self, **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def iter(cls, entity: str | UUID | AEntity, product_type: str = None, **kwargs) -> Iterator['AProduct']:
        if isinstance(entity, AEntity):
            entity = str(entity.id)
        for prod in api.pipe.iter_products(
            entity_id=entity,
                product_type=product_type
            ):
            yield cls(prod)

    @classmethod
    def create(cls,
               entity_id: str | UUID,
               name: str,
               product_type: str,
               variant: str,
               ) -> 'AProduct':
        product_id = api.pipe.create_product(name, entity_id, product_type, variant)
        return cls(product_id)

    def delete(self) -> None:
        raise NotImplementedError

    @classmethod
    def find(cls,
             entity_id: str | UUID,
             product_type: str = None,
             variant: str = None,
             **kwargs):
        data = api.pipe.find_product(entity_id=entity_id, product_type=product_type, variant=variant)
        if not data:
            return
        return cls(data)

    @classmethod
    def get_or_create(cls,
              entity_id: str | UUID,
              name: str,
              product_type: str,
              variant: str,):
        prod = cls.find(entity_id=entity_id, product_type=product_type, variant=variant)
        if not prod:
            prod = cls.create(entity_id=entity_id, name=name, product_type=product_type, variant=variant)
        return prod

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





