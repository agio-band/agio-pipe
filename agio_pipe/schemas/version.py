from uuid import UUID

from pydantic import BaseModel


class AVersionCreateSchema(BaseModel):
    product_id: UUID
    task_id: UUID
    version: str
    fields: dict|None


class PublishedFileFull(BaseModel):
    orig_path: str|None
    path: str
    relative_path: str
