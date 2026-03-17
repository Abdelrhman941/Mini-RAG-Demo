from .BaseController import BaseController
from .ProjectController import ProjectController
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..models import ProcessingEnum
import os


class ProcessController(BaseController):
    def __init__(self, project_id: str):
        super().__init__()
        self.project_id = project_id
        self.project_controller = ProjectController()
        self.project_path = self.project_controller.get_project_path(project_id=project_id)

    # ------------------ Get file extension from file_id ------------------
    def get_file_extension(self, file_id: str):
        return os.path.splitext(file_id)[-1]

    # ------------------ Validate file_id and return full path ------------------
    def validate_file_id(self, file_id: str) -> str:
        """Validate file_id and return full path."""
        # 1. check for unsafe characters to prevent path traversal
        if ".." in file_id or "/" in file_id or "\\" in file_id:
            raise ValueError(f"Invalid file_id: contains unsafe characters")
        # 2. build the full path
        file_path = os.path.join(self.project_path, file_id)
        # 3. check if the file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_id}")
        # 4. check that the path is within project_path (extra security)
        if not os.path.abspath(file_path).startswith(os.path.abspath(self.project_path)):
            raise ValueError(f"Invalid file_id: path traversal detected")
        return file_path

    # ------------------ Get appropriate file loader based on file extension ------------------
    def get_file_loader(self, file_id: str):
        file_path = self.validate_file_id(file_id)
        file_ext = self.get_file_extension(file_id=file_id)
        if file_ext == ProcessingEnum.TXT.value:
            return TextLoader(file_path, encoding="utf-8")
        if file_ext == ProcessingEnum.PDF.value:
            return PyMuPDFLoader(file_path)
        return None

    # ------------------ Load file content using the appropriate loader ------------------
    def get_file_content(self, file_id: str):
        try:
            loader = self.get_file_loader(file_id=file_id)
            if loader is None:
                raise ValueError(f"Unsupported file type: {file_id}")
            return loader.load()
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_id}")
        except Exception as e:
            raise Exception(f"Failed to load file content: {str(e)}")

    # ------------------ Process file content into chunks with metadata ------------------
    def process_file_content(
        self,
        file_content: list,
        file_id: str,
        chunk_size: int | None = None,
        overlap_size: int | None = None,
    ):
        chunk_size = chunk_size or self.settings.CHUNK_SIZE_DEFAULT
        overlap_size = overlap_size or self.settings.OVERLAP_SIZE_DEFAULT
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap_size,
            length_function=len,
        )
        texts = [doc.page_content for doc in file_content]
        metadatas = [doc.metadata for doc in file_content]
        for meta in metadatas:
            meta["file_id"] = file_id
        chunks = text_splitter.create_documents(texts, metadatas=metadatas)
        return chunks
