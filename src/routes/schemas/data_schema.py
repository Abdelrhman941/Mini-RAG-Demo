from pydantic import BaseModel
from typing import Optional
from core import get_settings

settings = get_settings()


class ProcessRequest(BaseModel):
    file_id: str
    chunk_size: Optional[int] = settings.CHUNK_SIZE_DEFAULT
    overlap_size: Optional[int] = settings.OVERLAP_SIZE_DEFAULT
    do_reset: Optional[bool] = False
