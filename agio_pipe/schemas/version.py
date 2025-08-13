from uuid import UUID

from pydantic import BaseModel


class PublishedFile(BaseModel):
    relative_path: str
    hash: str
    size: int


class AVersionFields(BaseModel):
    published_files: list[PublishedFile]


class AVersionCreateSchema(BaseModel):
    product_id: UUID
    task_id: UUID
    version: str
    fields: AVersionFields


class PublishedFileFull(BaseModel):
    path: str
    relative_path: str
    size: int = 0
    hash: str = None
