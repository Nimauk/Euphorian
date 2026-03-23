import os
import logging
import shutil
import requests
from pathlib import Path

logger = logging.getLogger(__name__)

def cleanup_files(*file_paths: str):
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
                logger.info(f"Deleted file: {path}")
            except Exception as e:
                logger.error(f"Failed to delete file {path}: {e}")

def get_absolute_path(relative_path: str) -> str:
    return str(Path(relative_path).absolute())

class FileManagerService:
    def download_remote_file(self, url: str, destination: str) -> bool:
        try:
            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                with open(destination, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                return True
            return False
        except Exception as e:
            logger.error(f"Error downloading remote file {url}: {e}")
            return False

file_manager = FileManagerService()
