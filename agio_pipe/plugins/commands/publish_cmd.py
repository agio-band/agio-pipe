import json
import logging
import traceback

import click

from agio.core.plugins.base_command import ACommandPlugin
from agio_pipe.publish import publish_core

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
        click.option("-i", "--instances", multiple=True, help='Instances to publish by name (default all)'),
        click.option("-o", "--output-file", help='JSON file to save report'),
    ]
    allow_extra_args = True

    def execute(self, scene_file: str, task_id: str, ui: bool, instances: tuple, output_file: str, **kwargs):
        if ui:
            self.open_dialog(scene_file, task_id, instances)
        else:
            if not scene_file:
                raise click.BadParameter('The scene_file not provided')
            extra_args, extra_kwargs = self.parse_extra_args(kwargs)
            if extra_args:
                raise click.BadParameter('Extra non keyword arguments provided but not supported')
            updated_instances = self.start_publish(scene_file, instances, **extra_kwargs)
            if updated_instances:
                click.secho(f'Result instances: {len(updated_instances)}', fg='green')
            else:
                click.secho('No publish result', fg='red')
            if output_file:
                self.create_report_file(output_file, scene_file, updated_instances)

    def open_dialog(self, scene_file: str|None, task_id: str,  instances: tuple[str]):
        click.secho('Open Publisher Dialog...', fg='yellow')
        from agio_publish_simple.ui import show_dialog
        from agio.tools import qt
        try:
            show_dialog(scene_file, instances, task_id)
        except Exception as e:
            traceback.print_exc()
            qt.message_dialog('Error', f'{type(e).__name__}: {e}', level='error')

    def start_publish(self, scene_file: str, instances: tuple, **kwargs):
        click.secho(f'Start Publish...', fg='yellow')
        # TODO pass options from pipeline settings
        core = publish_core.PublishCore()
        return core.start_publishing(scene_file=scene_file, selected_instances=instances, **kwargs)

    def create_report_file(self, output_file: str, scene_file: str, instances: list):
        report_data = {
            'scene_file': scene_file,
            'instances': [i.to_dict() for i in instances],
            # 'publish_session': None # TODO
        }
        if hasattr(output_file, 'write') and callable(getattr(output_file, 'write')):
            json.dump(report_data, output_file, indent=2)
        else:
            with open(output_file, 'w') as f:
                json.dump(report_data, f, indent=2)
