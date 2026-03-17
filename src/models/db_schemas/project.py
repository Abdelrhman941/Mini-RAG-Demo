from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
from bson.objectid import ObjectId
import re


class Project(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[ObjectId] = Field(None, alias="_id")
    project_id: str = Field(..., min_length=1)

    @field_validator('project_id')
    @classmethod
    def validate_project_id(cls, value: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]+$', value):
            raise ValueError('project_id must contain only alphanumeric, hyphens, and underscores')
        return value
