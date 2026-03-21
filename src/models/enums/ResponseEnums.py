from enum import Enum


class ResponseSignal(Enum):
    # ------------------ Health Check ------------------
    STATUS_HEALTHY = "healthy"
    STATUS_UNHEALTHY = "unhealthy"

    # ------------------ File Validation ------------------
    FILE_VALIDATED_SUCCESS = "file_validated_successfully"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    INVALID_FILENAME = "invalid_filename"

    # ------------------ File Upload ------------------
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"

    # ------------------ File Retrieval ------------------
    FILE_NOT_FOUND = "file_not_found"
    FILES_NOT_FOUND = "files_not_found"
    FILE_ID_ERROR = "file_id_error"

    # ------------------ File Processing ------------------
    PROCESSING_SUCCESS = "processing_success"
    PROCESSING_FAILED = "processing_failed"

    # ------------------ Project ------------------
    PROJECT_NOT_FOUND = "project_not_found"

    # ------------------ Chunk ------------------
    CHUNKS_NOT_FOUND = "chunks_not_found"

    # ------------------ Database ------------------
    DB_CONNECTION_SUCCESS = "database_connected"
    DB_CONNECTION_FAILED = "database_connection_failed"
