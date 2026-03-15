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
