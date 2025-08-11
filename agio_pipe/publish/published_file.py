from pydantic import BaseModel


class PublishedFile(BaseModel):
    path: str
    relative_path: str
    size: int = 0
    hash: str = None

