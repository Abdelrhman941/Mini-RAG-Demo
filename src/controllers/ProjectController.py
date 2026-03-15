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
