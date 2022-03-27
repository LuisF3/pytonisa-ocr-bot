from __future__ import annotations
from typing import Any
import boto3
from botocore.exceptions import ClientError
from bson import ObjectId
from bson.errors import InvalidId
import os

aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

class PytonisaDB:
    def __init__(self) -> None:
        ocr_requests_table_name = 'pytonisa-requests'

        self.client = boto3.resource('dynamodb', 'sa-east-1', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        self.ocr_requests: Table = Table(
            self.client.Table(ocr_requests_table_name))

    def close(self) -> None:
        pass


class DatabaseEntry:
    def __init__(self, _id: str=None) -> None:
        self._id: str = _id


class Table:
    def __init__(self, table_obj) -> None:
        self.table = table_obj

    def put_item(self, item: dict) -> dict:
        if '_id' not in item or bool(item['_id']) == False:
            item['_id'] = str(ObjectId())

        self.table.put_item(Item=item)

        return item

    def get_item(self, _id: str) -> dict:
        if not ObjectId.is_valid(_id):
            raise InvalidId('\'{_id}\' is not a valid ObjectId, it must be a 12-byte input or a 24-character hex string')

        try:
            response = self.table.get_item(Key={ '_id': _id })
        except ClientError as e:
            # log e.response['Error']['Message']
            raise e
        
        return response['Item'] 

    def update_item(self, _id: ObjectId, new_item: dict) -> dict:
        old_item = self.get_item(_id)
        
        for key, val in new_item.items():
            old_item[key] = val
        
        new_item = old_item
        return self.put_item(new_item)

