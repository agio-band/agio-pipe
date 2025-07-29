import json

import click
from agio.core.plugins.base_command import ACommandPlugin
from agio_pipe.publish.publish_core import PublishCore


class PublishCommand(ACommandPlugin):
    name = 'publish_cmd'
    command_name = 'pub'
    arguments = [
        click.argument('scene_file',
                       type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
                       nargs=1,
                       required=False),
        click.option("-i", "--ui", is_flag=True, help='Open Dialog'),
    ]

    def execute(self, scene_file: str, ui: bool):
        if ui:
            self.open_dialog(scene_file)
        else:
            if not scene_file:
                raise click.BadParameter('scene_file cannot be None')
            versions = self.start_publish(scene_file)
            if versions:
                click.secho('Created versions:', fg='green')
                for vers in versions:
                    click.secho(vers, fg='green')
            else:
                click.secho('No versions found', fg='red')

    def open_dialog(self, scene_file: str):
        click.secho('Open Dialog', fg='yellow')

    def start_publish(self, scene_file: str):
        click.secho(f'Start Publish...', fg='blue')
        # TODO pass options
        publish_core = PublishCore()
        return publish_core.start_publishing(scene_file=scene_file)
