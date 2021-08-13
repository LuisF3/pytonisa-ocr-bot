import asyncio
from typing import Union

from aio_pika import IncomingMessage
from bson.objectid import ObjectId
from motor.core import Collection, Database
from pytonisacommons import QueueMessage, log
from telethon import TelegramClient

telegram: Union[TelegramClient, None] = None
rabbitmq: Union[dict, None] = None
mongodb_db: Union[Database, None] = None


async def on_document_processed(message: IncomingMessage):
    if mongodb_db is None:
        log.warn(
            'on_document_processed called before mongodb is ready, sleeping 10 seconds')
        await asyncio.sleep(10)
        await message.nack()
        return
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

    await message.ack()


async def on_document_error(message: IncomingMessage):
    if mongodb_db is None:
        log.warn(
            'on_document_error called before mongodb is ready, sleeping 10 seconds')
        await asyncio.sleep(10)
        await message.nack()
        return
    collection: Collection = mongodb_db.ocr_request

    ocr_request_id = ObjectId(message.body.decode())
    log.info('Sending error for document of id ' + str(ocr_request_id))

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
        message='- ' + '\n- '.join(queue_message.errors)
    )

    await message.ack()
