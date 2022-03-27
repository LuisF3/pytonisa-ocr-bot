import asyncio
from typing import Union

from aio_pika import IncomingMessage
from bson.objectid import ObjectId
from pytonisacommons import QueueMessage, log, OcrMyPdfArgs
from telethon import TelegramClient

from pytonisacommons import PytonisaDB

telegram: Union[TelegramClient, None] = None
rabbitmq: Union[dict, None] = None
pytonisadb: PytonisaDB = None


async def on_document_processed(message: IncomingMessage):
    log.info('-'*20 + 'on_document_processed called' + '-'*20)

    if pytonisadb is None:
        log.warn(
            'on_document_processed called before mongodb is ready, sleeping 10 seconds')
        await asyncio.sleep(10)
        await message.nack()
        return

    ocr_request_id = str(ObjectId(message.body.decode()))
    log.info('Sending processed document of id ' + ocr_request_id)

    document: dict = pytonisadb.ocr_requests.get_item(ocr_request_id)
    queue_message = QueueMessage(**document)
    queue_message.ocr_args = OcrMyPdfArgs(**queue_message.ocr_args)

    await telegram.send_message(
        entity=queue_message.chat_id,
        message='OCR feito! Estamos fazendo upload do seu arquivo',
    )
    with open(queue_message.ocr_args.output_file, 'rb') as file:
        await telegram.send_message(
            entity=queue_message.chat_id,
            message='Aqui está!',
            reply_to=queue_message.message_id,
            file=file,
        )

    log.info('File sent')

    await message.ack()


async def on_document_error(message: IncomingMessage):
    if pytonisadb is None:
        log.warn(
            'on_document_error called before mongodb is ready, sleeping 10 seconds')
        await asyncio.sleep(10)
        await message.nack()
        return

    ocr_request_id = str(ObjectId(message.body.decode()))
    log.info('Sending error for document of id ' + ocr_request_id)

    document = pytonisadb.ocr_requests.get_item(ocr_request_id)
    queue_message = QueueMessage(**document)
    queue_message.ocr_args = OcrMyPdfArgs(**queue_message.ocr_args)

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
