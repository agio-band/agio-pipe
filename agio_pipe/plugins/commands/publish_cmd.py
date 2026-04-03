import json
import logging
import traceback

import click

from agio.core.plugins.base_command import ACommandPlugin
from agio_pipe.publish import publish_core
from agio.tools import modules
from agio.tools import qt

logger = logging.getLogger(__name__)


class PublishCommand(ACommandPlugin):
    name = 'publish_cmd'
    command_name = 'pub'
    arguments = [
        click.argument(
            'scene-file', required=False, type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True)
        ),
        click.option("-t", "--task-id", help='Task ID for ui context', required=False),
        click.option("-u", "--ui", is_flag=True, help='Open Publish Tool Dialog'),
        click.option("-i", "--instances", multiple=True, help='Instances to publish by name (default all)', required=False),
        click.option("-s", "--session-id", help='Suspended session ID', required=False),
        click.option("-d", "--dry-run", is_flag=True, help='Dry run'),
    ]
    allow_extra_args = True

    def execute(self, scene_file: str, task_id: str, ui: bool, instances: list[str], dry_run: str, session_id: str, **kwargs):
        if ui:
            self.open_dialog(scene_file, task_id, instances)
        else:
            if not scene_file and not session_id:
                raise click.BadParameter('The scene_file or session ID not provided')
            extra_args, extra_kwargs = self.parse_extra_args(kwargs)
            if extra_args:
                raise click.BadParameter('Extra non keyword arguments provided but not supported')
            self.start_publish(scene_file, instances, dry_run=dry_run, session_id=session_id, **extra_kwargs)

    def open_dialog(self, scene_file: str|None, task_id: str,  instances: list[str]):
        core = publish_core.PublishCore()
        engine = core.get_engine_plugin()
        ui_function_import_path = engine.open_ui_function
        if not ui_function_import_path:
            raise click.BadParameter(f'No ui_function provided for publish engine {engine}')
        func = modules.import_object_by_dotted_path(ui_function_import_path)
        try:
            click.secho(f'Open Publisher Dialog for task {task_id}...', fg='yellow')
            func(scene_file, instances, task_id)
        except Exception as e:
            traceback.print_exc()
            qt.show_message_dialog(str(e), title='Error', level='error')
            raise click.BadParameter(f'Publish UI opening failed {e}')

    def start_publish(self, scene_file: str, instances: list[str]|None, **kwargs):
        click.secho(f'Start Publish...', fg='yellow')
        # TODO pass options from pipeline settings
        core = publish_core.PublishCore()
        session = core.start_publishing(scene_file=scene_file, selected_instances=instances, **kwargs)
        click.echo(f'Publish Session ID: "{session.id}"')
