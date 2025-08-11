from agio.core.exceptions import AException


class DuplicateError(AException):
    detail = 'Duplicate error'


class PublishError(AException):
    detail = 'Publish error'