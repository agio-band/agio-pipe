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
        click.argument('scene_file',
                       type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
                       nargs=1,
                       required=False),
        click.option("-t", "--task_id", help='Task ID'),
        click.option("-u", "--ui", is_flag=True, help='Open Publish Tool Dialog'),
        click.option("-i", "--instances", multiple=True, help='Instances to publish by name'),
        click.option("-o", "--output_file", help='JSON file to write report'),
    ]

    def execute(self, scene_file: str, task_id: str,  ui: bool, instances: tuple, output_file: str):
        if ui:
            self.open_dialog(scene_file, task_id, instances)
        else:
            if not scene_file:
                raise click.BadParameter('The scene_file not provided')
            results = self.start_publish(scene_file, instances)
            if results:
                click.secho(f'Completed instances: {len(results)}', fg='green')
            else:
                click.secho('No versions found', fg='red')
            if output_file:
                self.create_report_file(output_file, scene_file, [inst.results for inst in results])

    def open_dialog(self, scene_file: str|None, task_id: str,  instances: tuple[str]):
        click.secho('Open Publisher Dialog...', fg='yellow')
        from agio_publish_simple.ui import show_dialog
        from agio_desk.tools import qt
        try:
            show_dialog(scene_file, instances, task_id)
        except Exception as e:
            qt.message_dialog('Error', str(e), level='error')

    def start_publish(self, scene_file: str, instances: tuple):
        click.secho(f'Start Publish...', fg='yellow')
        # TODO pass options
        core = publish_core.PublishCore()
        return core.start_publishing(scene_file=scene_file, selected_instances=instances)

    def create_report_file(self, output_file: str, scene_file: str, versions: list):

        report_data = {
            'scene_file': scene_file,
            'new_versions': versions,
            # 'publish_session': None # TODO
        }
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2)
