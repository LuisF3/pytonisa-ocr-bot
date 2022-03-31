import asyncio
import os

from aio_pika import Channel, Connection, Queue, connect_robust
from pytonisacommons import Queues, log, PytonisaDB, PytonisaFileStorage, PytonisaLocalFileStorage
from telethon import TelegramClient
from telethon.events import NewMessage

import messagehandlers
import queuehandlers
from messagehandlers import (help_lang_command, more_info_command, pdf_to_ocr,
                             start_command)
from queuehandlers import on_document_error, on_document_processed

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

rabbitmq_connection_string = os.getenv('RABBITMQ_CONN_STR')

if api_id is None or api_hash is None or bot_token is None or rabbitmq_connection_string is None:
    raise Exception('TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_BOT_TOKEN and RABBITMQ_CONN_STR must be not None')

async def start_telethon() -> TelegramClient:
    client: TelegramClient = await TelegramClient('pytonisa-telegram', int(api_id), api_hash).start(bot_token=bot_token)

    client.add_event_handler(start_command, NewMessage(
        incoming=True, pattern='/start'))
    client.add_event_handler(help_lang_command, NewMessage(
        incoming=True, pattern='/help_lang'))
    client.add_event_handler(more_info_command, NewMessage(
        incoming=True, pattern='/more_info'))
    client.add_event_handler(pdf_to_ocr, NewMessage(
        incoming=True, pattern='(^-)|(^$)', func=lambda e: e.file is not None and e.file.ext == '.pdf'))

    telethon = client
    return telethon


async def exit_telethon(telethon: TelegramClient) -> None:
    client: TelegramClient = telethon
    await client.disconnect()


async def start_rabbitmq(loop: asyncio.AbstractEventLoop) -> dict:
    connection = await connect_robust(rabbitmq_connection_string, loop=loop)
    channel: Channel = await connection.channel()

    queues: dict[str, Queue] = {}
    for queue in Queues:
        queues[queue.value] = await channel.declare_queue(queue.value, durable=True)

    rabbitmq = {
        'connection': connection,
        'channel': channel,
        'queues': queues
    }

    asyncio.gather(
        queues[Queues.PROCESSED.value].consume(
            on_document_processed),
        queues[Queues.ERROR.value].consume(
            on_document_error),
    )

    return rabbitmq


async def exit_rabbitmq(rabbitmq: dict) -> None:
    connection: Connection = rabbitmq['connection']
    await connection.close()


async def start_pytonisadb() -> PytonisaDB:
    return PytonisaDB()


async def exit_pytonisadb(pytonisadb: PytonisaDB) -> None:
    pytonisadb.close()


async def start_pytonisa_file_storage() -> PytonisaFileStorage:
    return PytonisaLocalFileStorage()


async def exit_pytonisa_file_storage(pytonisa_files: PytonisaLocalFileStorage) -> PytonisaFileStorage:
    pytonisa_files.close()


def main(loop: asyncio.AbstractEventLoop) -> None:
    telethon, pytonisadb, rabbitmq, pytonisa_files = loop.run_until_complete(
        asyncio.gather(
            start_telethon(),
            start_pytonisadb(),
            start_rabbitmq(loop),
            start_pytonisa_file_storage(),
        )
    )

    queuehandlers.telegram = telethon
    queuehandlers.rabbitmq = rabbitmq
    queuehandlers.pytonisadb = pytonisadb
    queuehandlers.pytonisa_files = pytonisa_files
    messagehandlers.rabbitmq = rabbitmq
    messagehandlers.pytonisadb = pytonisadb
    messagehandlers.pytonisa_files = pytonisa_files

    log.info('Bot initiated')

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(
            asyncio.gather(
                exit_telethon(telethon),
                exit_rabbitmq(rabbitmq),
                exit_pytonisadb(pytonisadb),
                exit_pytonisa_file_storage(pytonisa_files),
            )
        )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        main(loop)
    except:
        log.exception('Uncaugh exception...')
