import os
import asyncio

from logs import log
from handlers import start_command, help_lang_command, more_info_command, pdf_to_ocr 

from telethon import TelegramClient
from telethon.events import NewMessage

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

def exit_telethon(telethon):
    client = telethon
    client.disconnect()

async def start_rabbitmq():
    return 5

def exit_rabbitmq(rabbitmq):
    print(rabbitmq)


def main(loop: asyncio.AbstractEventLoop):
    telethon = loop.run_until_complete(start_telethon())
    rabbitmq = loop.run_until_complete(start_rabbitmq())

    log.info('Bot initiated')

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        exit_telethon(telethon)
        exit_rabbitmq(rabbitmq)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        main(loop)
    except:
        print('entrou')
        log.exception('Uncaugh exception...')
