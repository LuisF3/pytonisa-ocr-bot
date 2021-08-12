import os
import asyncio

from telethon.network.connection.connection import Connection

from configs.Logs import log
from MessageHandlers import start_command, help_lang_command, more_info_command, pdf_to_ocr
import MessageHandlers
from objects.Queues import Queues
from QueueHandlers import on_document_processed
import QueueHandlers

from telethon import TelegramClient
from telethon.events import NewMessage

from aio_pika import Connection, Channel, Queue, connect_robust

from motor.motor_asyncio import AsyncIOMotorClient

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

async def start_telethon() -> TelegramClient:
    client: TelegramClient = await TelegramClient('name', api_id, api_hash).start(bot_token=bot_token)

    client.add_event_handler(start_command, NewMessage(incoming=True, pattern='/start'))
    client.add_event_handler(help_lang_command, NewMessage(incoming=True, pattern='/help_lang'))
    client.add_event_handler(more_info_command, NewMessage(incoming=True, pattern='/more_info'))
    client.add_event_handler(pdf_to_ocr, NewMessage(incoming=True, pattern='(^-)|(^$)', func=lambda e: e.file is not None and e.file.ext == '.pdf'))

    telethon = client
    return telethon

async def exit_telethon(telethon: TelegramClient):
    client: TelegramClient = telethon
    await client.disconnect()

async def start_rabbitmq() -> dict:
    connection = await connect_robust("amqp://guest:guest@localhost/", loop=loop)
    channel: Channel = await connection.channel()

    queues: dict[str, Queue] = {}
    for queue in Queues:
        queues[queue.value] = await channel.declare_queue(queue.value, durable=True)

    rabbitmq = {
        'connection': connection,
        'channel': channel,
        'queues': queues
    }

    asyncio.create_task(
        queues[Queues.TO_PROCESS.value].consume(on_document_processed, no_ack=True)
    )

    return rabbitmq

async def exit_rabbitmq(rabbitmq: dict):
    connection: Connection = rabbitmq['connection']
    await connection.close()

async def start_mongodb() -> AsyncIOMotorClient:
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    
    mongodb = client
    return mongodb

async def exit_mongodb(mongodb: AsyncIOMotorClient):
    pass


def main(loop: asyncio.AbstractEventLoop) -> None:
    telethon, rabbitmq, mongodb = loop.run_until_complete(
        asyncio.gather(
            start_telethon(),
            start_rabbitmq(),
            start_mongodb(),
        )
    )

    QueueHandlers.telegram = telethon
    QueueHandlers.rabbitmq = rabbitmq
    MessageHandlers.rabbitmq = rabbitmq
    MessageHandlers.mongodb_db = mongodb.pytonisa
    QueueHandlers.telegram

    log.info('Bot initiated')

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(
            asyncio.gather(
                exit_telethon(telethon),
                exit_rabbitmq(rabbitmq),
                exit_mongodb(mongodb),
            )
        )

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        main(loop)
    except:
        print('entrou')
        log.exception('Uncaugh exception...')
