from ..core import Settings, get_settings
import os, secrets, string


class BaseController:
    def __init__(self, appSettings: Settings | None = None):
        self.settings = appSettings or get_settings()
        self.base_dir = os.path.dirname(os.path.dirname(__file__))
        self.files_dir = os.path.join(self.base_dir, "assets", "files")

    # ------------------ Utility method to generate random string for unique filenames ------------------
    def generate_random_string(self, length: int = 12) -> str:
        alphabet = string.ascii_lowercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))
