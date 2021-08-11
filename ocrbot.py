import os
import asyncio
from functools import partial

from telethon.network.connection.connection import Connection

from logs import log
from handlers import start_command, help_lang_command, more_info_command, pdf_to_ocr 

from telethon import TelegramClient
from telethon.events import NewMessage

from aio_pika import Connection, Channel, connect_robust

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

telethon = None
rabbitmq = None

async def start_telethon(rabbitmq):
    client: TelegramClient = await TelegramClient('name', api_id, api_hash).start(bot_token=bot_token)

    client.add_event_handler(start_command, NewMessage(incoming=True, pattern='/start'))
    client.add_event_handler(help_lang_command, NewMessage(incoming=True, pattern='/help_lang'))
    client.add_event_handler(more_info_command, NewMessage(incoming=True, pattern='/more_info'))
    client.add_event_handler(partial(pdf_to_ocr, rabbitmq), NewMessage(incoming=True, pattern='(^-)|(^$)', func=lambda e: e.file is not None and e.file.ext == '.pdf'))

    telethon = client
    return telethon

async def exit_telethon(telethon):
    client: TelegramClient = telethon
    await client.disconnect()

async def start_rabbitmq():
    connection = await connect_robust("amqp://guest:guest@localhost/", loop=loop)
    channel: Channel = await connection.channel()
    await channel.declare_queue('hello', auto_delete=True)

    rabbitmq = {
        'connection': connection,
        'channel': channel,
        'queues': [ 'hello' ],
    }

    return rabbitmq

async def exit_rabbitmq(rabbitmq):
    connection: Connection = rabbitmq['connection']
    await connection.close()


def main(loop: asyncio.AbstractEventLoop):
    rabbitmq = loop.run_until_complete(start_rabbitmq())
    telethon = loop.run_until_complete(start_telethon(rabbitmq))
    print(rabbitmq)

    log.info('Bot initiated')

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(exit_telethon(telethon))
        loop.run_until_complete(exit_rabbitmq(rabbitmq))

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        main(loop)
    except:
        print('entrou')
        log.exception('Uncaugh exception...')
