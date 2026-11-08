import os
from functools import cached_property

from agio.core.entities import ATask, AWorkspace, AWorkspaceRevision, AEntity
from agio.core.entities.profile import AProfile
from agio.core.entities.project import AProject
from agio.core.settings import get_local_settings
from agio.tools import env_names


class TaskContext:
    """
    This class provide API of current task environment and entities
    """

    def __str__(self):
        return ''

    def __repr__(self):
        return f'<TaskContext>'

    @property
    def task_id(self) -> str:
        task_id = os.environ.get(env_names.TASK_ID)
        if not task_id:
            raise EnvironmentError(f'Environment variable {env_names.TASK_ID} not set')

    @cached_property
    def task(self) -> ATask:
        return ATask.from_id(self.task_id)

    @property
    def entity_id(self) -> str:
        return self.task.entity_id

    @cached_property
    def entity(self) -> AEntity:
        return self.task.entity

    @property
    def project_id(self) -> str:
        return self.task.project_id

    @property
    def project(self) -> AProject:
        return self.task.project

    @cached_property
    def workspace(self) -> AWorkspace:
        return AWorkspace.current()

    @cached_property
    def workspace_revision(self) -> AWorkspaceRevision:
        return self.workspace.get_current_revision()

    @property
    def settings(self):
        return self.workspace.get_settings()

    @property
    def local_settings(self):
        return get_local_settings(self.project)

    @property
    def user(self) -> AProfile:
        return AProfile.current()
