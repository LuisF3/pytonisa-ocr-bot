import os
from logs import log
from handlers import start_command, help_lang_command, more_info_command, pdf_to_ocr 

from telethon import TelegramClient
from telethon.events import NewMessage

api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')

def main():
    with TelegramClient('name', api_id, api_hash).start(bot_token=bot_token) as client:
        client: TelegramClient

        client.add_event_handler(start_command, NewMessage(incoming=True, pattern='/start'))
        client.add_event_handler(help_lang_command, NewMessage(incoming=True, pattern='/help_lang'))
        client.add_event_handler(more_info_command, NewMessage(incoming=True, pattern='/more_info'))
        client.add_event_handler(pdf_to_ocr, NewMessage(incoming=True, pattern='(^-)|(^$)', func=lambda e: e.file is not None and e.file.ext == '.pdf'))

        log.info('Bot initiated')
        client.run_until_disconnected()

if __name__ == '__main__':
    try:
        main()
    except:
        print('entrou')
        log.exception('Uncaugh exception...')
