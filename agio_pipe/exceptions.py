from agio.core.exceptions import AException


class DuplicateError(AException):
    detail = 'Duplicate error'


class PublishError(AException):
    detail = 'Publish error'


class NoInstancesToPublishError(PublishError):
    detail = 'No instances to publish'


class InstanceDuplicateError(PublishError):
    detail = 'Instance duplicate error'
