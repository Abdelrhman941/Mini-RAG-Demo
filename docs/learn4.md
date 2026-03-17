```
docker/
src/
├── assets/
│   ├── files/
│   └── Mini-RAG.json
├── controllers/
│   ├── BaseController.py
│   ├── DataController.py
│   ├── ProcessController.py
│   ├── ProjectController.py
│   └── __init__.py
├── core/
│   ├── __init__.py
│   └── configs.py
├── models/
│   ├── db_schemas/
│   │   ├── __init__.py
│   │   ├── data_chunk.py
│   │   └── project.py
│   ├── enums/
│   │   ├── DBEnum.py
│   │   ├── ProcessingEnum.py
│   │   ├── ResponseEnums.py
│   │   └── __init__.py
│   ├── BaseDataModel.py
│   ├── ChunkModel.py
│   ├── ProjectModel.py
│   └── __init__.py
├── routes/
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── data_schema.py
│   ├── __init__.py
│   ├── base.py
│   └── data.py
├── .env.example
├── main.py
└── requirements.txt
```

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

## **docker/**
- use docker compose to run the application in a containerized environment.
- contains a Dockerfile and docker-compose.yml file.
- use .env file to manage environment variables for the application.

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

## **configs.py**
```python
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # ------------------ Application Configuration ------------------
    APP_NAME: str = "Mini-RAG"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "A mini RAG application for demo purposes."
    ENVIRONMENT: str = "local"

    # ------------------ File Upload Configuration ------------------
    FILE_ALLOWED_TYPES: list[str] = ["text/plain", "application/pdf"]
    FILE_MAX_SIZE: int = 10
    FILE_DEFAULT_CHUNK_SIZE: int = 512000  # bytes for reading uploaded files
    FILE_MAX_SIZE_SCALE: int = 1048576  # MB to bytes conversion (1MB = 1048576 bytes)
    CHUNK_SIZE_DEFAULT: int = 800
    OVERLAP_SIZE_DEFAULT: int = 100

    # ------------------ MongoDB Configuration ------------------
    MONGODB_URL: str
    MONGODB_DATABASE: str

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        env_file_encoding = "utf-8"

def get_settings():
    return Settings()
```

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

## **models/db_schemas/**
- contains Pydantic models that define the structure of data stored in MongoDB.
- includes models for projects and data chunks, which are the main entities in the application.

### **project.py**
```python
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
```

### **data_chunk.py**
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from bson.objectid import ObjectId


class DataChunk(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: Optional[ObjectId] = Field(None, alias="_id")
    chunk_text: str = Field(..., min_length=1)
    chunk_metadata: dict
    chunk_order: int = Field(..., ge=0)
    chunk_project_id: ObjectId
```

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

## **models/enums/DBEnum.py**
```python
from enum import Enum


class DataBaseEnum(Enum):
    # ------------------ Database collection names ------------------
    COLLECTION_PROJECT_NAME = "projects"
    COLLECTION_CHUNK_NAME = "chunks"
```

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

## **models/BaseDataModel.py**
```python
from ..core import get_settings


class BaseDataModel:
    def __init__(self, db_client: object):
        self.db_client = db_client
        self.app_settings = get_settings()
```

## **models/ProjectModel.py**
```python
from .BaseDataModel import BaseDataModel
from .db_schemas import Project
from .enums import DataBaseEnum as DB
import math


class ProjectModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DB.COLLECTION_PROJECT_NAME.value]

    # ------------------ Project operations [CRUD] ------------------
    async def create_project(self, project: Project):
        result = await self.collection.insert_one(project.model_dump(by_alias=True, exclude_unset=True))
        project.id = result.inserted_id
        return project

    # ------------------ Get or create project ------------------
    async def get_project_or_create_one(self, project_id: str):
        record = await self.collection.find_one({"project_id": project_id})
        if record is None:
            project = Project(project_id=project_id)
            project = await self.create_project(project=project)
            return project
        return Project(**record)

    # ------------------ Get all projects with pagination ------------------
    async def get_all_projects(self, page: int = 1, page_size: int = 10):
        total_documents = await self.collection.count_documents({})
        total_pages = math.ceil(total_documents / page_size) if total_documents > 0 else 1
        cursor = self.collection.find().skip((page - 1) * page_size).limit(page_size)
        projects = []
        async for document in cursor:
            projects.append(Project(**document))
        return projects, total_pages
```

## **models/ChunkModel.py**
```python
from .BaseDataModel import BaseDataModel
from .db_schemas import DataChunk
from .enums import DataBaseEnum as DB
from bson.objectid import ObjectId
from bson.errors import InvalidId
from pymongo import InsertOne


class ChunkModel(BaseDataModel):
    def __init__(self, db_client: object):
        super().__init__(db_client=db_client)
        self.collection = self.db_client[DB.COLLECTION_CHUNK_NAME.value]

    # ------------------ Chunk operations [CRUD] ------------------
    async def create_chunk(self, chunk: DataChunk):
        result = await self.collection.insert_one(chunk.model_dump(by_alias=True, exclude_unset=True))
        chunk.id = result.inserted_id
        return chunk

    # ------------------ Get chunk by id ------------------
    async def get_chunk(self, chunk_id: str):
        try:
            oid = ObjectId(chunk_id)
        except InvalidId:
            return None
        result = await self.collection.find_one({"_id": oid})
        if result is None:
            return None
        return DataChunk(**result)

    # ------------------ Insert many chunks in batches ------------------
    async def insert_many_chunks(self, chunks: list, batch_size: int = 100):
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            operations = [
                InsertOne(chunk.model_dump(by_alias=True, exclude_unset=True))
                for chunk in batch
            ]
            await self.collection.bulk_write(operations)
        return len(chunks)

    # ------------------ Delete chunks by project id ------------------
    async def delete_chunks_by_project_id(self, project_id: ObjectId):
        result = await self.collection.delete_many({
            "chunk_project_id": project_id
        })
        return result.deleted_count
```

```
┌─────────────────────┬──────────────────┬───────────────────┐
│     Feature         │  ProjectModel    │   ChunkModel      │
├─────────────────────┼──────────────────┼───────────────────┤
│ Collection          │ "projects"       │ "chunks"          │
│ Schema              │ Project          │ DataChunk         │
│ Purpose             │ Manage projects  │ Manage chunks     │
│ Main Operation      │ CRUD + Get/Create│ CRUD + Bulk ops   │
│ Bulk Insert         │ ❌ No            │ ✅ Yes (batched) │
│ Pagination          │ ✅ Yes           │ ❌ No            │
│ Error Handling      │ Basic            │ Advanced (try)    │
│ Pydantic Version    │ v1 (dict)        │ v2 (model_dump)   │
└─────────────────────┴──────────────────┴───────────────────┘
```

### 1️⃣ (Purpose)

#### ProjectModel 📁
```
- Manages project metadata
- Small number of records (hundreds)
- Focus: Get or create project
- Use case: User creates/views projects
```

#### ChunkModel 📄
```
- Manages text chunks (document pieces)
- Large number of records (thousands/millions)
- Focus: Bulk operations for speed
- Use case: Processing large documents
```

### 2️⃣ Methods

#### ProjectModel
```python
# 1️⃣ create_project
async def create_project(self, project: Project)
# Purpose: Insert one project
# Usage: When user creates a project

# 2️⃣ get_project_or_create_one ⭐
async def get_project_or_create_one(self, project_id: str)
# Purpose: Idempotent operation (safe to call multiple times)
# Usage: Ensure project exists before uploading files

# 3️⃣ get_all_projects ⭐
async def get_all_projects(self, page: int=1, page_size: int=10)
# Purpose: List projects with pagination
# Usage: Display projects in UI
```

#### ChunkModel
```python
# 1️⃣ create_chunk
async def create_chunk(self, chunk: DataChunk)
# Purpose: Insert one chunk
# Usage: Rarely used (prefer bulk)

# 2️⃣ get_chunk
async def get_chunk(self, chunk_id: str)
# Purpose: Retrieve specific chunk
# Usage: Get chunk details for display

# 3️⃣ insert_many_chunks ⭐⭐⭐
async def insert_many_chunks(self, chunks: list, batch_size: int = 100)
# Purpose: High-performance bulk insert
# Usage: After splitting document into chunks

# 4️⃣ delete_chunks_by_project_id ⭐
async def delete_chunks_by_project_id(self, project_id: ObjectId)
# Purpose: Cleanup when project deleted
# Usage: Cascade delete
```

```
┌─────────────────────────────────────────────────┐
│  Project (1)                                    │
│  ├─ _id: ObjectId("507f...")                    │
│  └─ project_id: "ecommerce-app"                 │
│                                                 │
│      │                                          │
│      │ One-to-Many                              │
│      │                                          │
│      ↓                                          │
│                                                 │
│  Chunks (Many)                                  │
│  ├─ Chunk 1                                     │
│  │  ├─ _id: ObjectId("abc...")                  │
│  │  └─ chunk_project_id: ObjectId("507f...")    │
│  │                                              │
│  ├─ Chunk 2                                     │
│  │  ├─ _id: ObjectId("def...")                  │
│  │  └─ chunk_project_id: ObjectId("507f...")    │
│  │                                              │
│  └─ ... (thousands more)                        │
└─────────────────────────────────────────────────┘
```

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>


## **routes\data.py**
```py
from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from core import Settings, get_settings
from controllers import DataController, ProcessController
from models import ResponseSignal as RS
import aiofiles, logging
from .schemas import ProcessRequest

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(prefix="/v1/data", tags=["data"])


# upload_data .... "same"


@data_router.post("/process/{project_id}")
async def process_endpoint(
    request: Request,
    project_id: str,
    process_request: ProcessRequest,
    appSettings: Settings = Depends(get_settings),
):
    try:
        file_id = process_request.file_id
        chunk_size = process_request.chunk_size or appSettings.CHUNK_SIZE_DEFAULT
        overlap_size = process_request.overlap_size or appSettings.OVERLAP_SIZE_DEFAULT
        do_reset = process_request.do_reset

        # ----------- 1. Get or create project
        project_model = ProjectModel(db_client=request.app.db_client)
        project_record = await project_model.get_project_or_create_one(project_id=project_id)

        # ----------- 2. Process file into chunks
        process_controller = ProcessController(project_id=project_id)
        file_content = process_controller.get_file_content(file_id=file_id)
        file_chunks = process_controller.process_file_content(
            file_content=file_content,
            file_id=file_id,
            chunk_size=chunk_size,
            overlap_size=overlap_size,
        )

        if not file_chunks:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": RS.PROCESSING_FAILED.value, "error": "No chunks generated"},
            )

        # ----------- 3. Build DataChunk records
        chunk_records = [
            DataChunk(
                chunk_text=chunk.page_content,
                chunk_metadata=chunk.metadata,
                chunk_order=i+1,
                chunk_project_id=project_record.id,
            )
            for i, chunk in enumerate(file_chunks)
        ]

        # ----------- 4. Reset if requested
        chunk_model = ChunkModel(db_client=request.app.db_client)
        if do_reset:
            await chunk_model.delete_chunks_by_project_id(project_id=project_record.id)

        # ----------- 5. Insert chunks
        inserted_count = await chunk_model.insert_many_chunks(chunks=chunk_records)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": RS.PROCESSING_SUCCESS.value,
                "file_id": file_id,
                "chunk_size": chunk_size,
                "overlap_size": overlap_size,
                "inserted_chunks": inserted_count,
            },
        )

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"signal": RS.PROCESSING_FAILED.value, "error": "File not found"},
        )
    except ValueError as e:
        logger.error(f"Invalid file type: {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": RS.PROCESSING_FAILED.value, "error": str(e)},
        )
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": RS.PROCESSING_FAILED.value},
        )
```

## **.env.example**
```env
# ------------------ Application Configuration ------------------
APP_NAME=Mini-RAG
APP_VERSION=0.1.0
APP_DESCRIPTION=A mini RAG application for demo purposes
ENVIRONMENT=local

# ------------------ File Upload Configuration ------------------
FILE_ALLOWED_TYPES=["text/plain", "application/pdf"]
FILE_MAX_SIZE=10
FILE_DEFAULT_CHUNK_SIZE=512000 # 512KB
CHUNK_SIZE_DEFAULT= 800
OVERLAP_SIZE_DEFAULT= 100

# ------------------ MongoDB Configuration ------------------
MONGODB_URL=mongodb://admin:your_secure_password_here@localhost:27007/?authSource=admin
MONGODB_DATABASE=put_your_database_name_here
```
