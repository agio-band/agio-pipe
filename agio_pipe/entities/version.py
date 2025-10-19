import os
from pathlib import Path
from typing import Self, Iterator
from uuid import UUID

from agio.core import api
from agio.core.entities import DomainBase
from agio.core import settings
from agio_pipe.entities import product

from agio_pipe.schemas.version import AVersionCreateSchema


class AVersion(DomainBase):
    domain_name = "version"

    VERSION_PADDING = os.getenv('AGIO_VERSION_NUMBER_PADDING', 7)

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
    def get_next_version_number(cls, product_id: str) -> int:
        return api.pipe.get_next_version_number(product_id)

    @classmethod
    def create(cls,
               product_id: str|UUID,
               task_id: str|UUID,
               fields: dict = None,
               version: int = None,
        ) -> Self:
        if version is None:
            version = cls.get_next_version_number(product_id)
        # add padding
        version = f"{version:0{cls.VERSION_PADDING}d}"
        schema = AVersionCreateSchema(
            **dict(
                product_id=product_id,
                task_id=task_id,
                version=version,
                fields=fields
            ),
        )
        version_id = api.pipe.create_version(**schema.model_dump())
        return AVersion(version_id)

    def delete(self) -> None:
        raise NotImplementedError()

    @classmethod
    def find(cls, **kwargs):
        raise NotImplementedError()

    def get_task(self):
        from agio_pipe.entities.task import ATask
        task = ATask.get_data(self._data['entity']['id'])
        return ATask(task)

    def to_dict(self):
        return dict(
            id=self.id,
            entity=self._data['entity'],
            fields=self._data['fields'],
            version=self.version_number,
            product=self.get_product().to_dict(),
        )

    def __get_context(self):
        from agio.core.settings import get_local_settings
        project = self.get_task().project
        local_settings = get_local_settings(project=project)
        context = dict(
            local_roots={k.name: k.path for k in local_settings.get('agio_pipe.local_roots')},
            project=project,
        )
        return context

    def iter_files_with_local_path(self):
        from agio_pipe.utils import path_solver
        files = self.fields['published_files']
        if files:
            project = self.get_task().project
            ws_settings = settings.get_workspace_settings(project.get_workspace())
            templates = ws_settings.get('agio_pipe.publish_templates')
            if templates is None:
                raise RuntimeError('No agio publish templates configured')
            templates = {tmpl.name: tmpl.pattern for tmpl in templates}
            context = self.__get_context()
            solver = path_solver.TemplateSolver(templates)
            project_root = solver.solve('project', context)
            for file in files:
                yield Path(project_root) / file['relative_path']
