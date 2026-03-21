from fastapi import APIRouter, Depends, UploadFile, status, Request
from fastapi.responses import JSONResponse
from ..core import Settings, get_settings
from ..controllers import DataController, ProcessController
from ..models import ResponseSignal as RS, ProjectModel, ChunkModel, DataChunk, AssetModel, Asset
from ..models.enums import AssetTypeEnum
import aiofiles, logging, os
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
    # ----------- 0. Get or create project
    project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
    project_record = await project_model.get_project_or_create_one(project_id=project_id)

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
            content={"signal": RS.FILE_UPLOAD_FAILED.value, "error": "Failed to save file to disk"},
        )
    except Exception as e:
        logger.error(f"Unexpected error while uploading file '{file_id}': {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"signal": RS.FILE_UPLOAD_FAILED.value, "error": "An unexpected error occurred"},
        )

    # ----------- 4. Store asset record in DB
    asset_model = await AssetModel.create_instance(db_client=request.app.db_client)
    asset_record = await asset_model.create_asset(
        Asset(
            asset_project_id=project_record.id,
            asset_type=AssetTypeEnum.FILE.value,
            asset_name=file_id,
            asset_size=os.path.getsize(file_path),
        )
    )

    # ----------- 5. Success response
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "signal": RS.FILE_UPLOAD_SUCCESS.value,
            "file_id": str(asset_record.id),
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
        chunk_size = process_request.chunk_size or appSettings.CHUNK_SIZE_DEFAULT
        overlap_size = process_request.overlap_size or appSettings.OVERLAP_SIZE_DEFAULT
        do_reset = process_request.do_reset

        # ----------- 1. Get or create project
        project_model = await ProjectModel.create_instance(db_client=request.app.db_client)
        project_record = await project_model.get_project_or_create_one(project_id=project_id)

        # ----------- 2. Resolve files to process via AssetModel
        asset_model = await AssetModel.create_instance(db_client=request.app.db_client)

        if process_request.file_id:
            asset_record = await asset_model.get_asset_record(
                asset_project_id=project_record.id,
                asset_name=process_request.file_id,
            )
            if asset_record is None:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"signal": RS.FILE_ID_ERROR.value},
                )
            project_files_ids = {asset_record.id: asset_record.asset_name}
        else:
            project_files = await asset_model.get_all_project_assets(
                asset_project_id=project_record.id,
                asset_type=AssetTypeEnum.FILE.value,
            )
            project_files_ids = {r.id: r.asset_name for r in project_files}

        if not project_files_ids:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"signal": RS.FILES_NOT_FOUND.value},
            )

        # ----------- 3. Reset chunks if requested
        chunk_model = await ChunkModel.create_instance(db_client=request.app.db_client)
        if do_reset:
            await chunk_model.delete_chunks_by_project_id(project_id=project_record.id)

        # ----------- 4. Process each file
        process_controller = ProcessController(project_id=project_id)
        inserted_count = 0
        processed_files = 0

        for asset_id, file_id in project_files_ids.items():
            file_content = process_controller.get_file_content(file_id=file_id)
            if file_content is None:
                logger.error(f"Could not read file content | file_id={file_id}")
                continue

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

            chunk_records = [
                DataChunk(
                    chunk_text=chunk.page_content,
                    chunk_metadata=chunk.metadata,
                    chunk_order=i + 1,
                    chunk_project_id=project_record.id,
                    chunk_asset_id=asset_id,          # ← linked to source asset
                )
                for i, chunk in enumerate(file_chunks)
            ]

            inserted_count += await chunk_model.insert_many_chunks(chunks=chunk_records)
            processed_files += 1

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "signal": RS.PROCESSING_SUCCESS.value,
                "chunk_size": chunk_size,
                "overlap_size": overlap_size,
                "inserted_chunks": inserted_count,
                "processed_files": processed_files,
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
