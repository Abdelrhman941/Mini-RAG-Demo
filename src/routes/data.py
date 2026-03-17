from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from ..core import Settings, get_settings
from ..controllers import DataController, ProcessController
from ..models import ResponseSignal as RS, ProjectModel, ChunkModel, DataChunk
import aiofiles, logging
from .schemas import ProcessRequest

logger = logging.getLogger("uvicorn.error")

data_router = APIRouter(prefix="/v1/data", tags=["data"])


@data_router.post("/upload/{project_id}", status_code=status.HTTP_201_CREATED)
async def upload_data(
    request: Request,
    project_id: str,
    file: UploadFile,
    appSettings: Settings = Depends(get_settings)
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
            content={"signal": RS.INVALID_FILENAME.value, "error": str(e)},
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
            while chunk := await file.read(appSettings.FILE_DEFAULT_CHUNK_SIZE):
                await f.write(chunk)
        logger.info(
            f"File uploaded | project_id={project_id} | "
            f"file_id={file_id} | size={file.size} bytes"
        )
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
            "original_filename": file.filename,
            "file_size": file.size,
            "file_id": file_id,
        },
    )


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
