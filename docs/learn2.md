```md
├── assets/
│   ├── files/                      # directory to store uploaded files
│   └── Mini-RAG.json
├── controllers/
│   ├── BaseController.py           # Base controller with common functionality [e.g., generate_random_string]
│   ├── DataController.py           # Controller for handling data and file operations [e.g., validate_uploaded_file, get_clean_file_name, generate_unique_filepath]
│   ├── ProjectController.py        # Controller for handling project-related operations [e.g., get_project_path]
│   └── __init__.py
├── core/
│   ├── __init__.py
│   └── configs.py
├── models/
│   ├── enums/ 
│   │   ├── __init__.py
│   │   └── ResponseEnums.py        # Enums for standardized response messages and status codes "fixed values"
│   └── __init__.py
├── routes
│   ├── __init__.py
│   ├── base.py                     # Base route[root , health check]
│   └── data.py                     # Route for handling data-related endpoints [e.g., file upload]
├── .env.example
├── .gitignore
├── main.py
└── requirements.txt
```

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

![image](images\image1.png)

<div style="width: 100%; height: 30px; background: linear-gradient(to right, rgb(235, 238, 212), rgb(235, 238, 212));"></div>

## **BaseController.py**
```py
from core.configs import Settings, get_settings
import os, secrets, string


class BaseController:
    def __init__(self, appSettings: Settings | None = None):
        self.settings = appSettings or get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.files_dir = os.path.join(self.base_dir, "assets", "files")

    def generate_random_string(self, length: int = 12) -> str:
        alphabet = string.ascii_lowercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
```

## **DataController.py**
```py
from .BaseController import BaseController
from .ProjectController import ProjectController
from fastapi import UploadFile
from models import ResponseSignal as RS
import re, os


class DataController(BaseController):
    """Controller for handling data and file operations."""

    def __init__(self):
        super().__init__()
        self.size_scale = 1048576  # convert MB to bytes
        self.project_controller = ProjectController()

    # ------------------ Validate uploaded file type and size ------------------
    def validate_uploaded_file(self, file: UploadFile):
        if file.content_type not in self.settings.FILE_ALLOWED_TYPES:
            return False, RS.FILE_TYPE_NOT_SUPPORTED.value
        if (
            file.size is not None
            and file.size > self.settings.FILE_MAX_SIZE * self.size_scale
        ):
            return False, RS.FILE_SIZE_EXCEEDED.value
        return True, RS.FILE_VALIDATED_SUCCESS.value

    # ------------------ Clean and sanitize filename ------------------
    def get_clean_file_name(self, orig_file_name: str):
        cleaned = orig_file_name.strip()
        cleaned = cleaned.replace(" ", "_")
        cleaned = re.sub(r"[^\w.-]", "", cleaned)
        if cleaned.startswith("."):
            cleaned = "file" + cleaned
        return cleaned or "unnamed_file"

    # ------------------- Generate unique filepath for uploaded file ------------------
    def generate_unique_filepath(self, orig_file_name: str | None, project_id: str):
        project_path = self.project_controller.get_project_path(project_id)
        cleaned_file_name = self.get_clean_file_name(orig_file_name) if orig_file_name else "unnamed_file"

        max_attempts = 100
        for _ in range(max_attempts):
            random_key = self.generate_random_string()
            new_filename = f"{random_key}_{cleaned_file_name}"
            new_file_path = os.path.join(project_path, new_filename)
            if not os.path.exists(new_file_path):
                return new_file_path, new_filename

        raise Exception("Failed to generate unique filename")
```

## **ProjectController.py**
```py
from .BaseController import BaseController
import os, re


class ProjectController(BaseController):
    """Controller for managing project directories."""

    PROJECT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

    def get_project_path(self, project_id: str) -> str:
        """Get or create project directory path."""
        project_id = project_id.strip()
        if not project_id:
            raise ValueError("Project ID cannot be empty")
        if ".." in project_id or "/" in project_id or "\\" in project_id:
            raise ValueError("Invalid project ID: contains unsafe characters")
        if not self.PROJECT_ID_PATTERN.match(project_id):
            raise ValueError(
                "Invalid project ID: must contain only alphanumeric, hyphens, and underscores"
            )

        project_dir = os.path.join(self.files_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir
```

## **configs.py**
```py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ------------------ Application Configuration ------------------
    APP_NAME: str = "Mini-RAG"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "A mini RAG application for demo purposes."
    ENVIRONMENT: str = "local"

    # ------------------ File Upload Configuration ------------------
    FILE_ALLOWED_TYPES: list[str] = ["text/plain", "application/pdf"]
    FILE_MAX_SIZE: int = 10
    FILE_DEFAULT_CHUNK_SIZE: int = 512000  # 512KB

    class Config:
        env_file = ".env"


def get_settings():
    return Settings()
```

## **models/enums/ResponseEnums.py**
```py
from enum import Enum


class ResponseSignal(Enum):
    # ------------------ Health check signals ------------------
    STATUS_HEALTHY = "healthy"
    STATUS_UNHEALTHY = "unhealthy"

    # ------------------ File upload signals ------------------
    FILE_VALIDATED_SUCCESS = "file_validate_successfully"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    INVALID_FILENAME = "invalid_filename"
```

## **routes\data.py**
```py
from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import JSONResponse
from core.configs import Settings, get_settings
from controllers import DataController
from models import ResponseSignal as RS
import aiofiles, logging

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(prefix="/v1/data", tags=["data"])


@data_router.post("/upload/{project_id}", status_code=status.HTTP_201_CREATED)
async def upload_data(
    project_id: str, file: UploadFile, app_settings: Settings = Depends(get_settings)
):
    data_controller = DataController()

    # ----------- 1. Validate file
    is_valid, result_signal = data_controller.validate_uploaded_file(file)
    if not is_valid:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"signal": result_signal}
        )

    # ----------- 2. Generate unique filepath
    try:
        file_path, file_id = data_controller.generate_unique_filepath(
            orig_file_name=file.filename,
            project_id=project_id
        )
    except ValueError as e:
        logger.error(f"Invalid project ID '{project_id}': {e}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"signal": "INVALID_PROJECT_ID", "error": str(e)},
        )
    except Exception as e:
        logger.error(f"Error generating filepath: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": RS.FILE_UPLOAD_FAILED.value},
        )

    # ----------- 3. Save file in chunks
    try:
        async with aiofiles.open(file_path, "wb") as f:
            while chunk := await file.read(app_settings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
        logger.info(f"File uploaded successfully: {file_id} to project {project_id}")
    except IOError as e:
        logger.error(f"IO error while saving file '{file_id}': {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": RS.FILE_UPLOAD_FAILED.value,
                "error": "Failed to save file to disk",
            },
        )
    except Exception as e:
        logger.error(f"Unexpected error while uploading file '{file_id}': {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "signal": RS.FILE_UPLOAD_FAILED.value,
                "error": "An unexpected error occurred",
            },
        )

    # ----------- 4. Success response
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "signal": RS.FILE_UPLOAD_SUCCESS.value,
            "file_id": file_id,
            "original_filename": file.filename,
            "file_size": file.size,
            "project_id": project_id,
        },
    )
```
