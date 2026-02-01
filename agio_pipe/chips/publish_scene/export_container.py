from __future__ import annotations
from typing import Any
from uuid import uuid4
from agio_pipe.entities.product import AProduct
from agio_pipe.entities.task import ATask
from agio_pipe.base_classes.export_container import ExportContainerBase


class ExportContainer(ExportContainerBase):

    def __init__(self, scene_object: Any, *args, **kwargs):
        super().__init__(scene_object, *args, **kwargs)
        self._init_entities()

    @classmethod
    def create_scene_object(cls, name: str, container_id: str = None) -> Any:
        return {'name': name, 'id': container_id or uuid4().hex}

    def validate(self, data: dict) -> None:
        pass

    def _init_entities(self):
        for field, id_field, cls in (
                ('task', 'task_id', ATask),
                ('product', 'product_id', AProduct),
            ):
            if field not in self.scene_object and id_field in self.scene_object:
                self.scene_object[field] = cls(self.scene_object[id_field])

    @property
    def name(self):
        return self.scene_object.get('name')

    @property
    def id(self):
        if 'id' not in self.scene_object:
            self.scene_object['id'] = uuid4().hex
        return self.scene_object['id']

    def set_id(self, value):
        self.scene_object['id'] = value

    def add_source(self, value: str):
        if 'sources' not in self.scene_object:
            self.scene_object['sources'] = []
        self.scene_object['sources'].append(value)

    def remove_source(self, value: str):
        if value in self.scene_object['sources']:
            self.scene_object['sources'].remove(value)
            return True
        return False

    def get_sources(self):
        return self.scene_object['sources']

    def set_product(self, product: AProduct):
        self.scene_object['product'] = product

    def get_product(self) -> AProduct|None:
        if 'product' in self.scene_object:
            return self.scene_object['product']
        elif 'product_id' not in self.scene_object:
            product = AProduct(self.scene_object['id'])
            self.scene_object['product'] = product
            return product
        else:
            raise ValueError('Product ID or Type name must be provided')

    def set_task(self, task: ATask):
        self.scene_object['task'] = task

    def get_task(self) -> ATask|None:
        if not 'task' in self.scene_object:
            if not 'task_id' in self.scene_object:
                return None
            self.scene_object['task'] = ATask(self.scene_object['task_id'])
        return self.scene_object.get('task')

    def set_options(self, options: dict):
        self.scene_object['options'] = options

    def get_options(self) -> dict:
        return self.scene_object.get('options', {})
