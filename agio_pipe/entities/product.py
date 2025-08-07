from typing import Self, Iterator
from uuid import UUID

from agio.core.domains import DomainBase, AEntity
from agio.core import api


class AProduct(DomainBase):
    type_name = "product"

    @classmethod
    def get_data(cls, object_id: str | UUID) -> dict:
        return api.pipe.get_product(object_id)

    def update(self, **kwargs) -> None:
        raise NotImplementedError

    @classmethod
    def iter(cls, entity: str | UUID | AEntity, product_type: str = None, **kwargs) -> Iterator[Self]:
        if isinstance(entity, AEntity):
            entity = str(entity.id)
        for prod in api.pipe.iter_products(
            entity_id=entity,
                product_type=product_type
            ):
            yield prod

    @classmethod
    def create(cls,
               entity: str | UUID | AEntity,
               name: str,
               product_type: str,
               variant: str,
               ) -> Self:
        data = api.pipe.create_product(name, entity, product_type, variant)
        return cls(**data)

    def delete(self) -> None:
        raise NotImplementedError

    @classmethod
    def find(cls,
             entity: str | UUID | AEntity,
             product_type: str = None,
             variant: str = None,
             **kwargs):
        pass





