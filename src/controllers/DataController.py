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
