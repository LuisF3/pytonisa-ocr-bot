import tempfile
import os

import boto3
from botocore.exceptions import ClientError

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

class PytonisaFileStorage:
    def upload_file(self, file_path: str) -> str:
        raise NotImplementedError()

    def download_file(self, id: str) -> str:
        raise NotImplementedError()

    def get_valid_path(self) -> str:
        raise NotImplementedError()

    def close(self) -> str:
        pass



class PytonisaLocalFileStorage(PytonisaFileStorage):
    def upload_file(self, file_path: str) -> str:
        return os.path.basename(file_path)

    def download_file(self, id: str) -> str:
        return os.path.join(self.get_valid_path(), id)
    
    def get_valid_path(self) -> str:
        return os.sep + 'pdfs'


class PytonisaS3Storage(PytonisaFileStorage):
    def __init__(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()

        self.bucket = "pytonisa-pdfs"
        self.s3 = boto3.client('s3', 'sa-east-1', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

    def upload_file(self, file_path: str) -> str:
        object_name = os.path.basename(file_path)

        try:
            self.s3.upload_file(file_path, self.bucket, object_name)
        except ClientError as e:
            return None
        return object_name

    def download_file(self, id: str) -> str:
        path = os.path.join(self.get_valid_path(), id)
        
        self.s3.download_file(self.bucket, id, path)

        return path

    def get_valid_path(self) -> str:
        return self.temp_dir.name

    def close(self) -> str:
        return self.temp_dir.cleanup()