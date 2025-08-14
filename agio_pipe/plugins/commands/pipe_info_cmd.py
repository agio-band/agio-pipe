import json

import click
from agio.core.plugins.base_command import ACommandPlugin


class PublishInfoCommand(ACommandPlugin):
    name = 'publish_info_cmd'
    command_name = 'pipeinfo'
    arguments = []

    def execute(self):
        from agio.core.domains import entity

        print('Entity classes:')
        for cls in sorted(entity.AEntity.__subclasses__(), key=lambda x: x.entity_class):
            if cls.entity_class:
                print(f'  {cls.entity_class:>10} | {cls.__module__}')
