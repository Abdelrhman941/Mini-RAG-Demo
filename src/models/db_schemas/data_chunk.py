from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from bson.objectid import ObjectId


class DataChunk(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1, max_length=10000)
    chunk_metadata: Dict = Field(default_factory=dict)
    chunk_order: int = Field(..., ge=0)
    chunk_project_id: ObjectId
    chunk_asset_id: Optional[ObjectId] = Field(default=None)

    @classmethod
    def get_indexes(cls):
        return [
            {
                "key": [("chunk_project_id", 1)],
                "name": "idx_chunk_project_id",
                "unique": False,
            },
            {
                "key": [("chunk_project_id", 1), ("chunk_order", 1)],
                "name": "idx_project_order",
                "unique": False,
            }
        ]
