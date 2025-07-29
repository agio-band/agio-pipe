from agio.core.exceptions import AException


class PublishError(AException):
    pass


class NoInstancesToPublishError(PublishError):
    pass

class InstanceDuplicateError(PublishError):
    pass

