from aio_pika import IncomingMessage
from telethon import TelegramClient
from typing import Union
from motor.core import Database, Collection
from bson.objectid import ObjectId
from pytonisacommons import log
from pytonisacommons import QueueMessage

telegram: Union[TelegramClient, None] = None
rabbitmq: Union[dict, None] = None
mongodb_db: Union[Database, None] = None


async def on_document_processed(message: IncomingMessage):
    collection: Collection = mongodb_db.ocr_request

    ocr_request_id = ObjectId(message.body.decode())
    log.info('Sending processed document of id ' + str(ocr_request_id))

    document = await collection.find_one(
        {'_id': ocr_request_id}
    )
    queue_message = QueueMessage(**document)

    await telegram.send_message(
        entity=queue_message.chat_id,
        message='OCR feito! Estamos fazendo upload do seu arquivo',
    )
    with open(queue_message.ocr_args['output_file'], 'rb') as file:
        await telegram.send_message(
            entity=queue_message.chat_id,
            message='Aqui está!',
            reply_to=queue_message.message_id,
            file=file,
        )


async def on_document_error(message: IncomingMessage):
    collection: Collection = mongodb_db.ocr_request

    ocr_request_id = ObjectId(message.body.decode())
    log.info('Sending processed document of id ' + ocr_request_id)

    document = await collection.find_one(
        {'_id': ocr_request_id}
    )
    queue_message = QueueMessage(**document)

    await telegram.send_message(
        entity=queue_message.chat_id,
        message='Infelizmente não foi possível reconhecer seu pdf. O(s) seguinte(s) erro(s) ocorreu(ram):',
        reply_to=queue_message.message_id,
    )
    await telegram.send_message(
        entity=queue_message.chat_id,
        message='\n'.join(queue_message.errors)
    )
    with open(queue_message.ocr_args['output_file'], 'rb') as file:
        await telegram.send_message(
            entity=queue_message.chat_id,
            message='Aqui está!',
            reply_to=queue_message.message_id,
            file=file,
        )
