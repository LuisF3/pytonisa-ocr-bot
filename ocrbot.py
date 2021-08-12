import os
import asyncio

from telethon.network.connection.connection import Connection

from logs import log
from handlers import start_command, help_lang_command, more_info_command, pdf_to_ocr
import handlers
from queues import Queues

from telethon import TelegramClient
from telethon.events import NewMessage

from aio_pika import Connection, Channel, connect_robust

from motor.motor_asyncio import AsyncIOMotorClient

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

async def start_telethon():
    client: TelegramClient = await TelegramClient('name', api_id, api_hash).start(bot_token=bot_token)

    client.add_event_handler(start_command, NewMessage(incoming=True, pattern='/start'))
    client.add_event_handler(help_lang_command, NewMessage(incoming=True, pattern='/help_lang'))
    client.add_event_handler(more_info_command, NewMessage(incoming=True, pattern='/more_info'))
    client.add_event_handler(pdf_to_ocr, NewMessage(incoming=True, pattern='(^-)|(^$)', func=lambda e: e.file is not None and e.file.ext == '.pdf'))

    telethon = client
    return telethon

async def exit_telethon(telethon):
    client: TelegramClient = telethon
    await client.disconnect()

async def start_rabbitmq():
    connection = await connect_robust("amqp://guest:guest@localhost/", loop=loop)
    channel: Channel = await connection.channel()

    for queue in Queues:
        await channel.declare_queue(queue.value, durable=True)

    rabbitmq = {
        'connection': connection,
        'channel': channel,
    }

    return rabbitmq

async def exit_rabbitmq(rabbitmq):
    connection: Connection = rabbitmq['connection']
    await connection.close()

async def start_mongodb():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    
    mongodb = client
    return mongodb

async def exit_mongodb(mongodb):
    pass


def main(loop: asyncio.AbstractEventLoop):
    telethon, rabbitmq, mongodb = loop.run_until_complete(
        asyncio.gather(
            start_telethon(),
            start_rabbitmq(),
            start_mongodb(),
        )
    )

    handlers.rabbitmq = rabbitmq
    handlers.mongodb_db = mongodb.pytonisa

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
