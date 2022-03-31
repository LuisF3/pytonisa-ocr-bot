import tempfile
import os

class PytonisaFileStorage:
    def upload_file(self, file_path: str) -> str:
        raise NotImplementedError()

    def download_file(self, id: str) -> str:
        raise NotImplementedError()

    def get_valid_path(self) -> str:
        return os.sep + 'pdfs'

    def close(self, id: str) -> str:
        pass


class PytonisaLocalFileStorage(PytonisaFileStorage):
    def upload_file(self, file_path: str) -> str:
        return file_path

    def download_file(self, id: str) -> str:
        return id
