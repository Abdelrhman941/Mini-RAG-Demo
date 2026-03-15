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
